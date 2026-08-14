# ThermoTwin physics kernel

This package is isolated from `pinn_heat`. Its first milestone implements the
constant-property, quasi-steady thermoelectric relations

\[
Q_c = \alpha I T_c - \tfrac{1}{2}I^2R - K(T_h-T_c),
\]

\[
Q_h = \alpha I T_h + \tfrac{1}{2}I^2R - K(T_h-T_c),
\]

\[
V = \alpha(T_h-T_c) + IR.
\]

Positive \(Q_c\) is heat removed from the cold node. Positive \(Q_h\) is heat
delivered to the hot node. Temperatures are expressed in kelvin.

The two-node transient right-hand side implements

\[
C_c\frac{dT_c}{dt}
=G_c(T_{c,\infty}-T_c)+\dot q_{c,\mathrm{ext}}-Q_c,
\]

\[
C_h\frac{dT_h}{dt}
=G_h(T_{h,\infty}-T_h)+\dot q_{h,\mathrm{ext}}+Q_h.
\]

It returns the instantaneous temperature rates but does not yet integrate
them through time. The package has no learned model or dependency on
`pinn_heat`.
