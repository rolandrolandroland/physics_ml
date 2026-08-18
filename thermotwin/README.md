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
the noise-only workflow does not add it. Lag, missing data, and
current-measurement error are not yet included.

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
