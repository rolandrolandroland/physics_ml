# ThermoTwin physics kernel

For a step-by-step explanation of the physics, code paths, conventional solver,
forward PINN, inverse parameter inference, tests, and current limitations, see
[`README_detailed.md`](README_detailed.md).

The governing project sequence, revised milestone definitions, current status,
and completion criteria are in [`ROADMAP.md`](ROADMAP.md).

## PINN showcase

For the shortest end-to-end demonstration, see
[`PINN_SHOWCASE.md`](PINN_SHOWCASE.md). One command trains the switched-current
physics-only and inverse PINNs and creates a focused six-panel evidence figure:

~~~bash
python3 -m thermotwin.pinn_showcase
~~~

The showcase highlights zero-label four-state forward prediction, recovery of
a hidden contact resistance from a 100 percent wrong initial guess,
reconstruction of two unobserved hot-side states, exact temperature continuity
at current switches, and parameter transfer to lower-amplitude and bipolar
controls. It also includes the conventional scalar baseline and states the
limits of the same-model synthetic comparison explicitly.

## Engineering decision showcase

The new CPU-first engineering workflow turns the validated model into four
decision-oriented synthetic experiments:

1. infer contact resistance, sensor lag, and two sensor biases using only the
   cold and hot exchanger temperatures, including missing turn-off readings;
2. reconstruct inaccessible face temperatures and transfer the inferred
   quantities to a withheld bipolar schedule;
3. compare optimized continuous and pulsed operation at equal delivered
   cooling after a periodic warm-up; and
4. select the next informative pulse under energy and temperature constraints,
   then use it as a standardized synthetic assembly fingerprint.

Run every experiment and generate the four-panel evidence figure with:

~~~bash
python3 -m thermotwin.engineering_showcase
~~~

The default output is
`thermotwin/figures/engineering_decision_showcase.png`. The main results are:

- exchanger-only inference recovers the 0.25 K/W hidden contact and estimates
  1.5 s sensor lag as 1.536 s, with every frozen truth inside its local 95%
  interval;
- the withheld current schedule has 0.00181 K accessible-sensor RMSE;
- optimized pulses have 21.8--27.6% lower COP at matched 2--8 W cooling and
  deliver 11.2--12.8% less cooling at matched power in the current lumped
  model;
- the constrained planner selects 0.8 A for 20 s and reduces linearized joint
  log-parameter RMSE by 82.2% versus the smallest feasible pulse; and
- a five-assembly synthetic batch is correctly separated into low-loss,
  reference-band, and elevated-loss contact groups.

The negative pulsing result is retained intentionally. It says that this
constant-property, fixed-reservoir model does not contain a mechanism that
overcomes the higher-current Joule penalty. It is not a claim about a different
physical device.

Each experiment has a complete question-to-result walkthrough:

- [`SPARSE_SENSOR_EXPERIMENT.md`](SPARSE_SENSOR_EXPERIMENT.md)
- [`CONTROL_COMPARISON_EXPERIMENT.md`](CONTROL_COMPARISON_EXPERIMENT.md)
- [`NEXT_EXPERIMENT_WALKTHROUGH.md`](NEXT_EXPERIMENT_WALKTHROUGH.md)
- [`ASSEMBLY_FINGERPRINT_EXPERIMENT.md`](ASSEMBLY_FINGERPRINT_EXPERIMENT.md)

## Efficiency and electrical-drive maps

Three linked experiments now turn the contact-aware model into an explicit
efficiency operating envelope:

1. a steady cooling/heating COP map over 0--1.5 A, 0--30 K external lift,
   three contact resistances, and the reduced no-explicit-contact topology;
2. an overlay of the existing seconds-scale pulse winners on the steady
   continuous-current COP envelope; and
3. a thermally averaged power-electronics layer that distinguishes ideal DC,
   smoothed PWM-derived current, and direct zero-to-peak current PWM.

Run the reports with:

~~~bash
python3 -m thermotwin.cop_operating_map_report
python3 -m thermotwin.pulse_operating_map_report
python3 -m thermotwin.pwm_power_electronics_report
~~~

The generic baseline shows that equal 0.25 K/W contacts reduce 3 W cooling COP
by about 19--35% over 0--25 K external lift relative to the reduced topology;
the target becomes infeasible at 30 K below the 1.5 A current bound. The
seconds-scale continuous baselines agree with the exact steady map within
0.04%, and their optimized pulse counterparts remain 21.8--27.6% below the
continuous COP envelope.

For electrical PWM, Peltier heat uses mean current while Joule heat uses
mean-square current. At 0.6 A mean current, direct 1.5 A chopping has 2.5 times
the DC Joule heat; the frozen 10% triangular-ripple smoothed case has only
1.0008 times. Converter input power is reported separately from module
terminal power so module COP and wall-plug COP are not confused.

The equations, settings, results, interpretation, and limits are documented in:

- [`COP_OPERATING_MAP_EXPERIMENT.md`](COP_OPERATING_MAP_EXPERIMENT.md)
- [`PULSE_OPERATING_MAP_EXPERIMENT.md`](PULSE_OPERATING_MAP_EXPERIMENT.md)
- [`PWM_POWER_ELECTRONICS_EXPERIMENT.md`](PWM_POWER_ELECTRONICS_EXPERIMENT.md)

The corresponding physics-and-code exercise sheets are
[`notes/19_cop_operating_map.md`](notes/19_cop_operating_map.md),
[`notes/20_pulse_operating_envelope.md`](notes/20_pulse_operating_envelope.md),
and
[`notes/21_pwm_power_electronics.md`](notes/21_pwm_power_electronics.md).

[`HARDWARE_VALIDATION_PROTOCOL.md`](HARDWARE_VALIDATION_PROTOCOL.md) defines
the measurement CSV and safety decisions needed for a future physical test.
No hardware result is claimed or synthesized.

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
or a `PiecewiseConstantCurrent` created with `constant`, `step`, `pulse`, or
`periodic_pulse`.
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
print(dataset.provenance.experiment.regime_name)
print(dataset.provenance.experiment.thermal_parameters)
~~~

This baseline has no noise, bias, lag, or missing readings. Its exercises are
in [notes/12_virtual_test_stand.md](notes/12_virtual_test_stand.md).

Every high-level generated dataset now includes self-contained provenance
without exposing its dense RK4 trajectory. The provenance records the complete
physical experiment, ground-truth thermoelectric and thermal parameters,
initial and reservoir temperatures, external heat inputs, duration,
integration step, current schedule, regime name, and train/validation/test
assignment. It also records the ordered observation pipeline. Applied Gaussian
noise includes its random seed; bias, lag, sampling, and outage steps include
their complete settings.

Run the compact whole-regime dataset audit with:

~~~bash
python3 -m thermotwin.dataset_quality
~~~

The frozen audit checks record counts, completeness, temperature/current
ranges, provenance, ground-truth availability, unique regime names, and the
presence of whole training, validation, and test experiments. It currently
reports 732 of 732 expected ideal observations and passes every provenance and
split-integrity check. Missing-observation datasets use the same summary to
report the exact unavailable count rather than treating absent readings as
zeros or `NaN` placeholders.

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

## Contact-aware forward PINN

The optional `thermotwin.contact_forward_pinn` module extends the learned
forward model to the explicit-contact topology. One network maps time to four
temperatures in the fixed order

~~~text
(cold TE face, hot TE face, cold exchanger, hot exchanger).
~~~

Its output transform enforces all four initial temperatures exactly. Training
uses the four face and exchanger energy-balance residuals; the RK4 contact
trajectory is withheld until validation. The initial contact PINN keeps every
physical parameter known, including both contact resistances, and accepts
constant current only. It therefore validates the four-state learned
architecture but does not yet perform contact-resistance inference.

Run the default 3,000-epoch CPU comparison with:

~~~bash
python3 -m thermotwin.contact_forward_pinn_report
~~~

The six-panel report compares the four temperature histories, their pointwise
errors, all four physics residuals, both contact temperature drops, and the
training loss. It is written by default to
`thermotwin/figures/contact_forward_pinn_comparison.png`.

With the frozen seed and reference experiment, the current default run gives a
final physics loss of about $1.13\times10^{-4}$ K$^2$/s$^2$. The cold-face,
hot-face, cold-exchanger, and hot-exchanger RMSE values are approximately
0.02498 K, 0.00348 K, 0.01509 K, and 0.00494 K, respectively. Small variation
across PyTorch versions or hardware is possible.

Physics and code exercises for this stage are in
[`notes/15_contact_forward_pinn.md`](notes/15_contact_forward_pinn.md).

## Piecewise switched-current contact PINN

The optional `thermotwin.piecewise_contact_forward_pinn` module extends the
four-state forward PINN to piecewise-constant current without forcing one
smooth network to represent discontinuous temperature derivatives. For the
established training pulse it uses three smooth subnetworks:

~~~text
0--5 s: 0 A  |  5--20 s: 1 A  |  20--60 s: 0 A
~~~

Each subnetwork begins exactly at the previous subnetwork's final four
temperatures. Temperatures are therefore continuous at both switches by
construction, while left- and right-side derivatives may differ. Current is
evaluated with the same right-continuous convention as RK4. Duration-weighted
midpoint collocation points exclude the switches, where a single classical
derivative is not defined.

Run the 5,000-epoch CPU comparison with:

~~~bash
python3 -m thermotwin.piecewise_contact_forward_pinn_report
~~~

The frozen result has exactly zero constructed boundary-temperature jump. Its
cold-face, hot-face, cold-exchanger, and hot-exchanger RMSE values against the
transition-splitting RK4 reference are approximately 0.008862 K, 0.001989 K,
0.009327 K, and 0.004628 K. RK4 temperatures remain withheld from training.

This stage validates switched-current forward dynamics with fixed contact
resistance. Its inverse extension below adds one trainable cold contact while
preserving the same piecewise architecture. Exercises are in
[`notes/17_piecewise_contact_forward_pinn.md`](notes/17_piecewise_contact_forward_pinn.md).

## Inverse cold-contact-resistance PINN

The optional `thermotwin.inverse_contact_resistance` module reuses the
four-temperature contact PINN and makes only the cold thermal contact
resistance trainable. A softplus transform keeps the inferred resistance
positive. All other physical parameters remain fixed at their synthetic truth.

The first controlled inverse baseline uses constant 1 A current and 13 ideal
cold-face/cold-exchanger observation times spaced 5 s apart. The loss combines
four normalized physics residuals with the two observed temperature histories.
Dense RK4 temperatures and both hot-side histories remain withheld from
training.

Run the 8,000-epoch CPU comparison and six-panel report with:

~~~bash
python3 -m thermotwin.inverse_contact_resistance_report
~~~

Starting from 0.50 K/W, the frozen run infers 0.250141 K/W for a hidden truth
of 0.250000 K/W, or about 0.056 percent relative error. The conventional
golden-section fit on the same sparse constant-current observations gives
0.250000 K/W. Substituting the PINN estimate into the conventional solver gives
all-sensor RMSE values of approximately 0.000087 K and 0.000145 K on the
previously defined validation and bipolar test pulse regimes.

The pulse-regime transfer check validates the inferred physical parameter, not
the learned temperature network: the first inverse PINN itself still trains on
one smooth constant-current experiment. It has not yet been exposed to noise,
bias, lag, missing observations, or uncertain physical coefficients.

The new physics and code exercises are in
[`notes/16_inverse_contact_resistance_pinn.md`](notes/16_inverse_contact_resistance_pinn.md).

## Piecewise inverse cold-contact-resistance PINN

The optional `thermotwin.piecewise_inverse_contact_resistance` module combines
the switched-current temperature architecture with one positive trainable cold
contact resistance shared by all three time segments. Its frozen ideal problem
uses the established 0--1--0 A training pulse and 61 paired cold-face and
cold-exchanger observation times at 1 s spacing. Dense temperatures and both
hot-side histories remain withheld from training.

The normalized loss combines all four energy-balance residuals with the cold
observation mismatch. The observation term has weight 20 to condition the
joint neural/parameter optimization; this is a numerical choice, not
additional data or a claim about sensor uncertainty. Exact segment chaining
still forces all four temperature jumps to zero.

Run the default 8,000-epoch CPU comparison and eight-panel report with:

~~~bash
python3 -m thermotwin.piecewise_inverse_contact_resistance_report
~~~

Starting from 0.50 K/W, the frozen run infers 0.250519 K/W for a hidden truth
of 0.250000 K/W, or about 0.208 percent relative error. The conventional fit on
the identical pulse observations gives 0.250000 K/W. Dense neural temperature
RMSE values are approximately 0.00670, 0.00287, 0.00180, and 0.00262 K for the
cold face, hot face, cold exchanger, and hot exchanger. Transferring the PINN
parameter through the conventional solver gives all-sensor RMSE values of
approximately 0.000322 K and 0.000534 K on the unseen validation and bipolar
test pulses.

This remains an ideal same-model baseline. It does not yet train on noise,
bias, lag, missing observations, restricted sensors, uncertain coefficients,
or hardware data. Exercises are in
[`notes/18_piecewise_inverse_contact_resistance.md`](notes/18_piecewise_inverse_contact_resistance.md).

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
