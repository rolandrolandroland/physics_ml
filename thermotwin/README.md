# ThermoTwin physics kernel

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

The package has no learned model or dependency on `pinn_heat`.

## Learning notes

The user-authored derivations, explanations, predictions, and corrections are
organized in [`notes/00_index.md`](notes/00_index.md). These notes are kept
separate from this concise package reference so they can document the reasoning
and learning process in detail.
