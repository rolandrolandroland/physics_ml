# 04 — Transient right-hand side

Status: `Not started`

## Learning objective

> Explain how the two physical energy balances become a function that returns
> instantaneous temperature rates.

## Inputs and outputs

| Code value | Physical meaning | Units | Constant, state, or input? |
| --- | --- | --- | --- |
|  |  |  |  |

## Algorithm in my own words

> Describe the calculation order without copying the implementation. Include
> how $Q_c$, $Q_h$, reservoir heat, net node heat, and temperature rates
> are obtained.

## Return ordering

> State the return order and explain how you will prevent cold/hot states from
> being accidentally swapped in a future ODE solver.

## Hand calculation

> Choose one complete operating point and calculate $dT_c/dt$ and
> $dT_h/dt$ by hand. Compare the results with `two_node_rhs`.

## Parameter validation

> Explain why capacitances must be positive and why conductances may be zero
> but not negative in this model.

## Limiting cases and test mapping

> For each transient test, write the physical prediction first and then explain
> why the assertion is an appropriate check.

## What this function does not do

> Explain the difference between evaluating an instantaneous RHS and integrating
> a trajectory through time. List other effects not yet represented.

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
