# 01 — Sign conventions

Status: `Not started`

## Learning objective

> Explain what every positive and negative quantity means physically, without
> relying only on memorized equation signs.

## System boundary and node diagram

> Draw or describe the cold node, thermoelectric module, hot node, and both
> reservoirs. Add arrows showing the positive directions of heat and current.

For the following system arranged from left to right:
Cold reservoir <==> cold node <==> thermoelectric module <==> hot node <==> hot reservoir
For Qc and Qh, positive values represent heat transfer in the cold-to-hot direction.
## My sign conventions

| Quantity                  | Meaning when positive                                                                                         | Meaning when negative                           | Units                                   |
|---------------------------|---------------------------------------------------------------------------------------------------------------|-------------------------------------------------|-----------------------------------------|
| $I$                       | Conventional current enters P and leaves N, Peltier effect pumps heat from cold to hot, given positive $\alpha$ | Conventional current enters N and leaves P. Given positive α, the Peltier effect pumps heat from hot to cold.    | Amps, or charge per second  (coulombs/s) |
| $V$                       | terminal P has higher potential than terminal N                                               | Terminal N has higher potential than terminal P | Volts, or Joule/coulomb                 |
| $Q_c$                     | Heat leaves cold node into module                                                                             | Heat enters cold node from module               | Watt (J/s)                              |
| $Q_h$                     | Heat enters hot node from module                                                                              | Heat leaves hot node for module                 | Watt (J/s)                              |
| $T_h-T_c$                 | Hot node is hotter than cold node                                                                             | Cold node is hotter than hot node               | Kelvin                                  |
| $\dot q_{c,\mathrm{ext}}$ | Heat is entering cold node                                                                                    | Heat is leaving cold node                       | Watt (J/s)                                  |
| $\dot q_{h,\mathrm{ext}}$ | Heat is entering hot node                                                                                     | Heat is leaving hot node                        | Watt (J/s)                                      |
Positive VI means electrical power enters the module; negative VI means electrical power leaves the module.
## Zero-current prediction

> For $I=0$ and $T_h>T_c$, predict the signs of $Q_c$, $Q_h$, $V$,
> and $VI$. Explain the actual direction of every energy flow.

If I is 0 and $T_h > T_c$, then $Q_c$ and $Q_h$ will both be negative. This means that heat will flow from hot to cold, which makes sense because that is how the system works without any external current. 
## Current-reversal prediction

> Predict which terms change sign when current reverses and which do not.

$Q_c$ and $Q_h$ can change sign if current changes direction, assuming a large enough Peltier contribution. V is externally applied, so it will not  change. $T_h$ - $T_c$ might change sign, given enough time. $\dot q_{c,\mathrm{ext}}$ and $\dot q_{h,\mathrm{ext}}$ won't change initially. 
## Connection to the code

> List the functions and tests that encode or verify these conventions. Explain
> how their argument and return-value names correspond to the diagram above.

The cold_side_heat and hot_side_heat functions, which use the peltier_heating, joule_heating, and heat_leak functions encode these conventions
## Limiting-case checks

> Work through equal face temperatures, reversed face temperatures, and zero
> current. State which signs you expect before evaluating the code.

If $T_c = T_h = T$, then the conduction heat term is 0.

$Q_c = \alpha I T_c - \frac{1}{2}I^2R$ and $Q_h = \alpha I T_c + \frac{1}{2}I^2R$
For positive current, $Q_h$ will definitely increase and $Q_c$ will increase, given a high enough Seebeck coefficient relative to the current and resistance. 

If $T_c > T_h$, you may still have Peltier heating and Joule heating, but the conductive heating will be reversed
## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
