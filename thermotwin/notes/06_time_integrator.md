# 06 — Time integrator

Status: `Not started`

## Learning objectives

By the end of these exercises, I should be able to:

1. Distinguish an instantaneous right-hand side from a time trajectory.
2. Explain why the temperature rates change during a simulation.
3. Trace one RK4 step through the implementation.
4. Connect numerical checks to physical limiting cases.
5. Recognize when a result may depend on the chosen time step.

Work through one block at a time. Write predictions before evaluating the code,
include units in every calculation, and record corrections rather than erasing
the original reasoning.

## Reference current-step experiment

Use these values unless an exercise states otherwise:

| Quantity | Value | Units |
| --- | ---: | --- |
| $\alpha$ | 0.05 | V/K |
| $R$ | 2.0 | ohm |
| $K$ | 0.5 | W/K |
| $C_c$ | 100 | J/K |
| $C_h$ | 200 | J/K |
| $G_c$ | 2.0 | W/K |
| $G_h$ | 4.0 | W/K |
| $T_c(0)$ | 300 | K |
| $T_h(0)$ | 300 | K |
| $T_{c,\infty}$ | 300 | K |
| $T_{h,\infty}$ | 300 | K |
| $I$ | 1.0 | A |
| $\dot q_{c,\mathrm{ext}}$ | 0 | W |
| $\dot q_{h,\mathrm{ext}}$ | 0 | W |

The reference run lasts 60 s with a requested step of 0.1 s.

---

## Block 1 — From rates to a trajectory

### Exercise 1: RHS versus integrator

In my own words, explain the difference between:

- calling `two_node_rhs` once; and
- calling `integrate_two_node` for 60 seconds.

Address the input and output units, whether time advances, and why one call to
the RHS cannot produce an entire trajectory.

**My answer:**

### Exercise 2: First-step prediction

Reproduce the initial calculations of $Q_c$, $Q_h$, $dT_c/dt$, and $dT_h/dt$.
Then use a simple Euler estimate over 0.1 s:

$$
T(t+\Delta t) \approx T(t) + \Delta t\frac{dT}{dt}.
$$

Predict $T_c(0.1)$ and $T_h(0.1)$ before looking at the RK4 result. Explain why
the Euler and RK4 answers should be close but not exactly identical.

**My calculations and prediction:**

### Exercise 3: Identify every feedback mechanism

After a short time, suppose $T_c<300$ K and $T_h>300$ K. For each item below,
state its sign and whether it tends to accelerate or oppose the existing
temperature change:

1. $G_c(T_{c,\infty}-T_c)$
2. $G_h(T_{h,\infty}-T_h)$
3. $K(T_h-T_c)$
4. $\alpha I T_c$
5. $\alpha I T_h$
6. $I^2R$

Identify which terms remain constant and which change with the state.

**My answer:**

### Checkpoint 1

Ask Codex to review Exercises 1–3 before continuing.

---

## Block 2 — Transient science and limiting cases

### Exercise 4: What steady state means

A steady state does not require every heat flow to be zero. Starting from the
two node balances, set both temperature rates to zero and write the resulting
two equations. Explain in words what must balance at each node.

Do not solve the simultaneous equations yet. Predict whether the reference
steady temperatures will satisfy $T_c<300$ K and $T_h>300$ K, and justify the
prediction term by term.

**My equations and prediction:**

### Exercise 5: Passive insulated module

Set $I=0$, both reservoir conductances to zero, and both external heat inputs
to zero. Begin with $T_h>T_c$.

1. Predict the signs of both temperature rates.
2. Add the two node energy balances.
3. Determine whether $C_cT_c+C_hT_h$ should remain constant.
4. Predict the common final temperature if the nodes eventually equilibrate.
5. Explain why the final temperature is capacitance-weighted rather than a
   simple average when $C_c\ne C_h$.

**My derivation and prediction:**

### Exercise 6: Reservoir time scales

For a single node with no thermoelectric or external heat, use

$$
C\frac{dT}{dt}=G(T_\infty-T)
$$

to show by units that $C/G$ has units of time. Calculate $C_c/G_c$ and
$C_h/G_h$ for the reference parameters. Explain what those values suggest
about whether a 60 s simulation is short or long relative to reservoir
response.

State why these single-node time scales are useful guides but are not the exact
time constants of the coupled thermoelectric system.

**My calculation and interpretation:**

### Checkpoint 2

Ask Codex to review Exercises 4–6 before continuing.

---

## Block 3 — RK4 and the implementation

### Exercise 7: Trace the trajectory container

Read `TemperatureTrajectory` and the start and end of `integrate_two_node` in
`thermotwin/transient.py`.

1. What do `time`, `cold`, and `hot` contain?
2. Why must the three tuples always have the same length?
3. Why is the initial condition stored before the integration loop begins?
4. For a duration of 0.25 s and requested step of 0.1 s, predict the complete
   `time` tuple.
5. Explain why the last step is shorter in that example.

**My code trace:**

### Exercise 8: Trace one RK4 step

Treat the coupled temperature state as $y=[T_c,T_h]$ and the RHS as
$f(y)=[dT_c/dt,dT_h/dt]$. Map each implemented value to:

$$
k_1=f(y_n),
$$

$$
k_2=f\left(y_n+\frac{\Delta t}{2}k_1\right),
$$

$$
k_3=f\left(y_n+\frac{\Delta t}{2}k_2\right),
$$

$$
k_4=f(y_n+\Delta t\,k_3).
$$

Then explain:

1. Why `k1`, `k2`, `k3`, and `k4` each contain two rates.
2. Why both temperatures must be updated together at every trial state.
3. Why `k2` and `k3` are evaluated at different predicted midpoint states.
4. Why the final weighting is $1,2,2,1$.
5. What units each `k` has and what units $\Delta t\,k$ has.

**My code-to-equation mapping:**

### Exercise 9: Constant-rate limiting case

Suppose the RHS returns the same two rates for every possible temperature.

1. Determine the relationship among $k_1$, $k_2$, $k_3$, and $k_4$.
2. Simplify the RK4 update.
3. Explain why RK4 and Euler then give the same result.
4. Find the unit test that creates this condition with zero thermoelectric and
   reservoir effects plus constant external heat inputs.
5. Explain what a failure of that test would imply about the integrator.

**My derivation and test mapping:**

### Exercise 10: Validation and failure behavior

Read the checks at the beginning of `integrate_two_node` and answer:

1. Why must the requested time step be positive and finite?
2. Why may duration be zero but not negative?
3. What trajectory should a zero-duration run return?
4. How could an excessively large but positive time step produce a misleading
   result even though it passes validation?
5. Why is repeating a run with smaller steps an important numerical check?

**My answer:**

### Checkpoint 3

Ask Codex to review Exercises 7–10 before running step-size experiments.

---

## Block 4 — Numerical verification and interpretation

### Exercise 11: Step-size refinement

Before running anything, predict whether the final temperatures should change
substantially when the step is reduced from 0.2 s to 0.1 s and then 0.05 s.
Run the same physical experiment at all three steps and record:

| Requested step | Final $T_c$ | Final $T_h$ | Change from previous run |
| ---: | ---: | ---: | ---: |
| 0.2 s |  |  | — |
| 0.1 s |  |  |  |
| 0.05 s |  |  |  |

Explain whether the results appear converged. Distinguish numerical agreement
from evidence that the physical model itself is accurate.

### Exercise 12: Interpret the current-step trajectory

Plot or inspect $T_c(t)$, $T_h(t)$, and $T_h(t)-T_c(t)$ for the reference run.
Answer:

1. Are the initial directions consistent with the hand calculation?
2. Do the slopes weaken, strengthen, or reverse over time?
3. Which changing terms explain that behavior?
4. Has the system reached steady state by 60 s? Define the numerical evidence
   you would use rather than judging only by the appearance of a plot.
5. What result would indicate a possible sign error?

**My results and interpretation:**

### Exercise 13: Design the next minimal experiment

Choose exactly one change: reverse the current, set the current to zero,
remove reservoir coupling, add a cold-side heat load, or double one thermal
capacitance.

Before running, state:

1. The single question the experiment answers.
2. Which initial rate or trajectory feature should change.
3. Which quantities must remain fixed for a fair comparison.
4. Which limiting-case or energy check should still hold.

Record the full design in `05_forward_experiments.md` before evaluating it.

**My proposed experiment:**

---

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
