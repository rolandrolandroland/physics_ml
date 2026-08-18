# ThermoTwin physics kernel

For a step-by-step explanation of the physics, code paths, conventional solver,
forward PINN, inverse parameter inference, tests, and current limitations, see
[`README_detailed.md`](README_detailed.md).

This package is isolated from `pinn_heat`. Its first milestone implements the
constant-property, quasi-steady thermoelectric relations

$$
Q_c = \alpha I T_c - \tfrac{1}{2}I^2R - K(T_h-T_c),
$$

$$
Q_h = \alpha I T_h + \tfrac{1}{2}I^2R - K(T_h-T_c),
$$

$$
V = \alpha(T_h-T_c) + IR.
$$

Positive $Q_c$ is heat removed from the cold node. Positive $Q_h$ is heat
delivered to the hot node. Temperatures are expressed in kelvin.

The two-node transient right-hand side implements

$$
C_c\frac{dT_c}{dt}
=G_c(T_{c,\infty}-T_c)+\dot q_{c,\mathrm{ext}}-Q_c,
$$

$$
C_h\frac{dT_h}{dt}
=G_h(T_{h,\infty}-T_h)+\dot q_{h,\mathrm{ext}}+Q_h.
$$

The `two_node_rhs` function returns the instantaneous temperature rates.
`integrate_two_node` advances those rates through time with a fixed-step,
classical fourth-order Runge--Kutta method. It accepts either a constant current
or a `PiecewiseConstantCurrent` created with `constant`, `step`, or `pulse`.
Integration steps end exactly at scheduled current transitions so an abrupt
switch is not averaged across one RK4 interval. Reservoir temperatures and
external heat inputs remain constant during a run. The function returns the
sampled time, cold-temperature, and hot-temperature histories and uses only the
Python standard library.

For constant inputs, `two_node_steady_state` independently sets both node
energy-storage rates to zero and solves the resulting two-by-two algebraic
system. Comparing a long RK4 trajectory with this solution checks that the
transient solver approaches the correct equilibrium rather than merely giving
similar answers at several time steps.

`evaluate_trajectory` post-processes every temperature sample into aligned
histories of current, temperature difference, $Q_c$, $Q_h$, terminal voltage,
electrical power, and cooling COP. COP is reported as `None` when electrical
power is zero and the ratio is undefined.

`constant_current_reference_experiment` freezes the agreed first comparison
case: 1 A for 60 s, equal 300 K initial and reservoir temperatures, and a 0.1 s
RK4 step. `run_two_node_experiment` returns both the temperature trajectory and
its derived diagnostics so learned and conventional results use identical
inputs.

## Contact-aware four-node model

The separate [contact_transient.py](contact_transient.py) module adds cold and
hot thermoelectric-face nodes, cold and hot heat-exchanger nodes, and one
thermal contact resistance on each side. Contact heat is

$$
\dot q_{\mathrm{contact},c}
=\frac{T_{x,c}-T_c}{R_{\mathrm{contact},c}},
\qquad
\dot q_{\mathrm{contact},h}
=\frac{T_h-T_{x,h}}{R_{\mathrm{contact},h}}.
$$

The four balances store energy separately in both faces and both exchangers.
The thermoelectric heat rates use the face temperatures; fixed reservoirs and
external loads act on the exchanger nodes. The integrate_four_node_contact
function supports the same scalar, step, and pulse current inputs as the
two-node integrator.

The original two-node API remains unchanged and is the reduced model to use
when contacts are intentionally omitted or lumped. Do not represent that
choice by passing zero contact resistance to the four-node equations.

The model derivation and code exercises are in
[notes/10_contact_aware_transient.md](notes/10_contact_aware_transient.md).
Exercises for the frozen experiment, diagnostics, COP definitions, energy
checks, comparison, and sweep are in
[notes/11_contact_reference_diagnostics.md](notes/11_contact_reference_diagnostics.md).

The frozen contact reference uses 1 A for 60 s, equal 0.25 K/W contacts,
50+50 J/K cold capacitance, and 100+100 J/K hot capacitance. It produces
aligned histories of both contact drops and heat rates, $Q_c$, $Q_h$, voltage,
power, module COP, exchanger-delivered COP, and whole-system energy closure.

Generate the two-node comparison and symmetric contact-resistance sweep with:

~~~bash
python3 -m thermotwin.contact_report
~~~

By default, generated reports are written under `thermotwin/figures/`. That
directory is ignored by Git because the figures can be reproduced from the
committed code. Pass `--output PATH` to override the location deliberately.

## Ideal virtual test stand

The [virtual_test_stand.py](virtual_test_stand.py) module separates dense
synthetic truth from the observations that a later inverse model is allowed to
see. The first ideal baseline attaches one named sensor to each of the four
contact-model nodes and records exact temperatures every 1 s. The hidden RK4
trajectory still uses a 0.1 s step.

Each long-form observation stores its time, sensor name, modeled location,
temperature in kelvin, and aligned current in amperes. The sampler supports
arbitrary sensor subsets, includes the exact final time, linearly interpolates
when a requested measurement lies between stored truth states, and uses the
same right-continuous current convention as the integrator.

~~~python
from thermotwin import run_ideal_contact_reference_test_stand

dataset = run_ideal_contact_reference_test_stand()
print(len(dataset.measurement_times))  # 61
print(len(dataset.observations))       # 244
~~~

This baseline has no noise, bias, lag, or missing readings. Its exercises are
in [notes/12_virtual_test_stand.md](notes/12_virtual_test_stand.md).

## Reproducible temperature noise

The separate [measurement_noise.py](measurement_noise.py) module applies
independent zero-mean Gaussian errors to temperature readings without changing
the immutable ideal dataset. The generic learning baseline uses a 0.05 K
standard deviation and random seed 2026. It is synthetic and is not a claim
about any physical sensor's accuracy.

The noise configuration supports a default standard deviation plus named
per-sensor overrides. Times, currents, sensor names, locations, units, and
record counts remain unchanged. A zero standard deviation is tested as the
exact ideal-data limiting case.

~~~python
from thermotwin import run_noisy_contact_reference_test_stand

result = run_noisy_contact_reference_test_stand()
print(result.noise_model)
print(result.dataset.observations[:4])
~~~

The same seed reproduces the same readings. Different seeds create different
synthetic trials. Fixed bias is available as a separate transformation below;
the noise-only workflow does not add it. Lag and missingness are separate
transformations below. Current-measurement error is not yet included.

## Fixed temperature bias

The [measurement_bias.py](measurement_bias.py) module adds constant
per-sensor temperature offsets without modifying its input dataset. The
generic bias-only baseline applies +0.10 K to `cold_face_sensor` and 0 K to the
other three sensors. This is a controlled learning case, not a calibrated
instrument offset.

~~~python
from thermotwin import run_biased_contact_reference_test_stand

result = run_biased_contact_reference_test_stand()
print(result.bias_model)
print(result.dataset.observations_for("cold_face_sensor")[:3])
~~~

Zero bias exactly reproduces the input dataset. A combined helper applies the
frozen Gaussian noise and bias baselines while retaining both configurations:

~~~python
from thermotwin import run_noisy_biased_contact_reference_test_stand

result = run_noisy_biased_contact_reference_test_stand()
print(result.noise_model)
print(result.bias_model)
~~~

Unlike zero-mean random noise, a fixed sensor bias does not diminish when many
readings are averaged.

## First-order sensor lag

The [measurement_lag.py](measurement_lag.py) module represents a sensor that
relaxes toward the modeled node temperature with a first-order time constant.
The generic baseline gives `cold_face_sensor` a 2 s time constant and leaves
the other sensors instantaneous. The first sensor reading is initialized to
the first node temperature.

~~~text
a = exp(-time_step / time_constant)
lagged_temperature = a * previous_lagged_temperature
                     + (1 - a) * current_node_temperature
~~~

The dense 0.1 s truth signal is filtered before readings are sampled every
1 s. This prevents changing the output sampling interval from changing the
underlying simulated sensor response. The combined workflow then applies
fixed bias and Gaussian noise after lag.

~~~python
from thermotwin import run_lagged_contact_reference_test_stand

result = run_lagged_contact_reference_test_stand()
print(result.lag_model)
print(result.dataset.observations_for("cold_face_sensor")[:3])
~~~

For the frozen cooling transient, the lagged cold-face reading remains warmer
than the instantaneous face temperature. The difference peaks near 0.377 K
and is about 0.058 K at 60 s. This output filter does not feed heat back into
the thermal model and is not a calibrated physical sensor model.

## Deterministic missing observations

The [measurement_missingness.py](measurement_missingness.py) module represents
known sensor outages by omitting unavailable long-form records. The generic
baseline removes `cold_face_sensor` readings from 20 through 30 s, inclusive.
It removes 11 of the original 244 records, leaving 50 cold-face readings and
233 total records. All 61 measurement times remain because the other three
sensors continue reporting.

~~~python
from thermotwin import run_missing_contact_reference_test_stand

result = run_missing_contact_reference_test_stand()
print(len(result.dataset.observations))  # 233
print(result.missingness_model)
~~~

Missing readings are absent rows, not 0 K values, `NaN` values, or
interpolated replacements. The complete synthetic measurement workflow uses:

~~~text
truth -> lag -> sampling -> bias -> noise -> remove unavailable readings
~~~

The sensor's lag state continues evolving during the communication outage.
Missingness changes neither the hidden thermal trajectory nor any retained
record. An empty outage configuration exactly reproduces the complete input
dataset. This first deterministic outage is a reproducible learning case, not
a model of random or temperature-dependent hardware failure.

Consolidated physics, code, validation, and experiment-design exercises for
sampling, temperature noise, fixed bias, sensor lag, and missing observations
are in
[notes/13_measurement_imperfections.md](notes/13_measurement_imperfections.md).

## Cold contact-resistance inference experiment

The dependency-free
[contact_resistance_inference.py](contact_resistance_inference.py) module
performs the first conventional inference of one cold thermal contact
resistance. Every other physical parameter remains fixed. Ideal observations
from the cold face and cold exchanger enter an equal-weight least-squares
loss; both hot-side histories are retained as independent consistency checks.

Whole experiments are split by operating regime:

- training: a +1 A pulse from 5 to 20 s;
- validation: a +0.6 A pulse from 10 to 30 s; and
- testing: a held-out +1 A/−1 A bipolar schedule.

A bounded golden-section search over 0.05 to 1.0 K/W recovers the hidden
0.25 K/W resistance as 0.250000002 K/W in 42 loss evaluations. Fitted-pair
RMSE remains below 2.3e-9 K on all three regimes.

~~~bash
python3 -m thermotwin.contact_resistance_inference
~~~

The near-floating-point errors are expected because the same noise-free model
generates and fits the data. They validate the controlled inference workflow,
not hardware accuracy or robustness to uncertain parameters and measurement
imperfections.

The complete standalone walkthrough is
[CONTACT_RESISTANCE_EXPERIMENT.md](CONTACT_RESISTANCE_EXPERIMENT.md). Physics,
code, optimization, validation, and interpretation exercises are in
[notes/14_contact_resistance_experiment.md](notes/14_contact_resistance_experiment.md).

### Repeated Gaussian-noise robustness study

The follow-on
[contact_resistance_noise_study.py](contact_resistance_noise_study.py) module
repeats the same fit for 100 independently seeded synthetic trials. Every
temperature sensor receives independent zero-mean Gaussian noise with a
0.05 K standard deviation. Only the cold face and cold exchanger enter the
fit; bias, lag, missingness, current error, and model mismatch remain disabled
so this stage isolates random temperature noise.

~~~bash
python3 -m thermotwin.contact_resistance_noise_study
~~~

Use `--trials 5` for a faster exploratory run. The optional
`--first-seed` and `--noise-standard-deviation` arguments create another
reproducible synthetic study without changing the frozen default.

The frozen seeds beginning at 2026 produce:

| Metric | 100-trial result |
| --- | ---: |
| Mean inferred resistance | 0.249782542 K/W |
| Sample standard deviation | 0.004116544 K/W |
| Mean parameter bias | -0.000217458 K/W |
| Parameter RMSE | 0.004101678 K/W |
| Empirical 5th--95th percentiles | 0.243722770--0.256246405 K/W |
| Search-bound hits | 0 |

The mean fitted-pair error relative to noisy observations remains close to the
imposed 0.05 K noise scale. Relative to the hidden ideal temperatures, the
mean errors are 0.003580 K on training, 0.002800 K on validation, and
0.004655 K on test. These values describe one reproducible same-model Monte
Carlo study. The percentile range is an empirical distribution across those
100 trials, not a formal confidence interval or a hardware uncertainty claim.

Run the focused ideal-inference and noise-study tests with:

~~~bash
python3 -m unittest \
  tests.test_contact_resistance_inference \
  tests.test_contact_resistance_noise_study
~~~

### Bias, lag, missingness, and sensor-availability studies

Five dependency-free follow-on studies isolate the remaining measurement
effects before combining them:

~~~bash
python3 -m thermotwin.contact_resistance_bias_study
python3 -m thermotwin.contact_resistance_lag_study
python3 -m thermotwin.contact_resistance_missingness_study
python3 -m thermotwin.contact_resistance_sensor_study
python3 -m thermotwin.contact_resistance_combined_study
~~~

The fixed-bias cases show systematic parameter shifts that averaging cannot
remove. A +0.10 K cold-face bias produces 0.208885 K/W, while the same bias on
the cold exchanger produces 0.272817 K/W. Equal +0.10 K bias on both cold
sensors still produces 0.228450 K/W because the loss uses absolute
temperatures as well as their difference.

Sensor lag is applied to dense 0.1 s truth before 1 s output sampling. A 2 s
cold-exchanger lag produces 0.270766 K/W, and 2 s lag on both cold sensors
produces 0.270847 K/W. The resistance shift cannot reproduce the full dynamic
lag, so held-out residuals remain.

The missingness study removes both cold-sensor readings around each regime's
nonzero-to-zero current transition. Exact remaining data still recover the
truth, but the local training sum-of-squares curvature falls from 304.858 with
complete readings to 216.496 for a plus-or-minus 2 s outage and 133.466 for a
plus-or-minus 5 s outage. Removing five equilibrium readings per sensor leaves
the curvature unchanged, confirming that switch-adjacent records are more
informative than an equal number of steady records.

The restricted-sensor study also recovers the truth in the exact same-model
limit, but its information metric exposes large practical differences:

| Available sensors | Training information curvature |
| --- | ---: |
| Cold face and cold exchanger | 304.858 |
| Cold face only | 208.858 |
| Cold exchanger only | 95.999 |
| Hot pair only | 1.943 |
| All four sensors | 306.800 |

The hot pair adds less than 1 percent to the cold pair's information about the
cold contact resistance in this experiment.

The frozen combined pipeline is

~~~text
dense lag -> sample -> bias -> noise -> turn-off missingness -> restrict sensors
~~~

It uses 2 s cold-face lag, +0.10 K cold-face bias, 0.05 K independent Gaussian
noise, plus-or-minus 2 s turn-off outages, and only the cold pair. Across the
same 100 seeds used by the noise-only study, it produces:

| Metric | Combined result |
| --- | ---: |
| Mean inferred resistance | 0.201589285 K/W |
| Sample standard deviation | 0.005680841 K/W |
| Mean parameter bias | -0.048410715 K/W |
| Parameter RMSE | 0.048739579 K/W |
| Empirical 5th--95th percentiles | 0.192003358--0.210809525 K/W |
| Search-bound hits | 0 |

The systematic bias is much larger than the random trial spread. Repetition
therefore characterizes random variation but does not correct an incorrect
measurement model. All results remain same-model synthetic studies rather
than hardware uncertainty claims. The full derivations, case definitions, and
limitations are in
[CONTACT_RESISTANCE_EXPERIMENT.md](CONTACT_RESISTANCE_EXPERIMENT.md), with
exercises in
[notes/14_contact_resistance_experiment.md](notes/14_contact_resistance_experiment.md).

## First forward PINN

The optional `thermotwin.forward_pinn` module contains a small PyTorch network
that maps time to $(T_c,T_h)$. It trains on the two energy-balance residuals;
RK4 temperatures are used only afterward for validation. Its output transform
enforces both initial temperatures exactly rather than treating them as a soft
penalty.

The initial model intentionally supports only constant current. This keeps the
first learned problem smooth and provides a controlled baseline before adding
current switches, inverse parameters, or experimental data. CPU is the default
device. Set `device="mps"` or `device="auto"` in `ForwardPINNConfig` to use
Apple MPS when it is available.

Install the optional dependency and run the reference training with:

```bash
python3 -m pip install -r thermotwin/requirements-pinn.txt
python3 -m thermotwin.forward_pinn
```

Generate a four-panel comparison of the RK4 and PINN trajectories, pointwise
temperature errors, physics residuals, and training loss with:

```bash
python3 -m thermotwin.forward_pinn_report
```

The core solver remains independent of PyTorch and `pinn_heat`.

## First inverse parameter problem

The optional `thermotwin.inverse_thermal_conductance` module treats the module
thermal conductance $K$ as one positive trainable parameter. The baseline uses
noise-free synthetic $T_c$ and $T_h$ observations every 5 s from the 60 s
reference experiment. All other physical parameters and inputs remain fixed
at their known values.

The temperature network and $K$ are trained jointly. The loss combines the two
ODE residuals at dense collocation points with errors at the 13 sparse
temperature snapshots. A softplus transform keeps the inferred conductance
positive. Dense RK4 temperatures remain separate validation data.

Run the baseline with:

```bash
python3 -m thermotwin.inverse_thermal_conductance
```

This noise-free, single-parameter recovery is a controlled identifiability
baseline. It does not yet establish robustness to measurement noise, sparse
sensors, simultaneous unknown parameters, model mismatch, or hardware data.

Exercises for deriving, tracing, testing, and interpreting this inverse problem
are in
[`notes/09_inverse_thermal_conductance.md`](notes/09_inverse_thermal_conductance.md).

## Learning notes

The user-authored derivations, explanations, predictions, and corrections are
organized in [`notes/00_index.md`](notes/00_index.md). These notes are kept
separate from this concise package reference so they can document the reasoning
and learning process in detail.
