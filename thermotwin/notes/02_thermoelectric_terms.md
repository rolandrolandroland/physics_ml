# 02 — Thermoelectric terms

Status: `Not started`

## Learning objective

> Explain the origin, current dependence, direction, and units of every term in
> the single-block thermoelectric equations.

## Equations from memory

> Write $Q_c$, $Q_h$, and $V$ without copying them. Define every symbol.

## Term-by-term explanation

| Term | Physical mechanism | Current dependence | Direction or sign | Units |
| --- |--------------------| --- | --- | --- |
| Cold-side Peltier term | $\alpha IT_c$      |  |  |  |
| Hot-side Peltier term | $\alpha I T_h$     |  |  |  |
| Joule term | $\frac{1}{2}I^2 R$ |  |  |  |
| Conductive term |                    |  |  |  |
| Seebeck voltage term |                    |  |  |  |

## Equal division of Joule heating

> Explain why this model assigns half of $I^2R$ to each face. Identify this
> as a modeling assumption and describe when it might be inadequate.

## Energy identity

> Derive $Q_h-Q_c$ step by step and connect it to $VI$. Explain what the
> result means for a control volume around the thermoelectric module.

## Excessive-current prediction

> Explain why useful Peltier cooling cannot dominate indefinitely as current
> increases. Derive the current that maximizes $Q_c$ at fixed temperatures.

## Hand calculation

> Choose one set of parameter values. Calculate every term, $Q_c$, $Q_h$,
> $V$, electrical power, and COP by hand before comparing with the code.

## Connection to the code and tests

> Map each mathematical term to its function and identify which test checks it.

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
