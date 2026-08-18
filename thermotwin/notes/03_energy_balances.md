# 03 — Energy balances

Status: `Not started`

## Learning objective

> Derive both node balances from the first law and explain every term's sign.

## Control volumes

> Define what is included in the cold node, hot node, and thermoelectric module.
> State where thermal energy can be stored in this model.

## Thermal capacitance

> Starting from the relationship between internal energy and temperature,
> explain why the storage term is $C\,dT/dt$. Check its units.

## Cold-node derivation

> List every heat flow entering and leaving the cold node, then derive its
> transient balance one step at a time.

## Hot-node derivation

> List every heat flow entering and leaving the hot node, then derive its
> transient balance one step at a time.

## Reservoir/contact terms

> Explain the signs of $G_c(T_{c,\infty}-T_c)$ and
> $G_h(T_{h,\infty}-T_h)$ using both warmer- and colder-reservoir examples.

## Combined-node balance

> Add the cold and hot balances. Simplify the thermoelectric contribution and
> explain why internal heat transport cancels from the combined balance.

## Limiting cases

> Predict the temperature-rate signs for equilibrium, insulated nodes with
> $I=0$, a positive external heat load, and doubled thermal capacitances.

## Connection to the code and tests

> Map each balance term to the transient RHS and identify the energy test.

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
