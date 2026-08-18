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
python3 -m thermotwin.forward_pinn_report \
  --output forward_pinn_comparison.png
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
