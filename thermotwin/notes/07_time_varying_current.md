# 07 — Time-varying current

Status: `Not started`

## Learning objectives

By the end of these exercises, I should be able to:

1. Describe constant, step, pulse, and multi-transition current schedules.
2. Explain which physical quantities can jump at a current transition and
   which must remain continuous.
3. Predict how switching current changes Peltier heat, Joule heat, voltage,
   electrical power, temperature rates, and COP.
4. Explain why RK4 steps must end exactly at discontinuities.
5. Trace the schedule through the control, integration, and diagnostics code.
6. Design a pulse experiment that answers one well-defined physical question.

Work through one block at a time. Make every prediction before evaluating the
code. Include units and state all assumptions.

## Reference model and schedules

Use the parameters from `06_time_integrator.md`:

| Quantity | Value | Units |
| --- | ---: | --- |
| $\alpha$ | 0.05 | V/K |
| $R$ | 2.0 | ohm |
| $K$ | 0.5 | W/K |
| $C_c$ | 100 | J/K |
| $C_h$ | 200 | J/K |
| $G_c$ | 2.0 | W/K |
| $G_h$ | 4.0 | W/K |
| $T_c(0)=T_h(0)$ | 300 | K |
| $T_{c,\infty}=T_{h,\infty}$ | 300 | K |
| Both external heat inputs | 0 | W |

Use these schedules unless an exercise states otherwise:

- **Step:** 0 A before 10 s and 1 A from 10 s onward.
- **Pulse:** 0 A for $t<10$ s, 1 A for $10\le t<30$ s, and 0 A for
  $t\ge30$ s.
- **Simulation duration:** 60 s.

The schedules are right-continuous: the new value applies at the transition
time itself.

---

## Block 1 — Schedule meaning and boundary conventions

### Exercise 1: Translate code into a timeline

Read `PiecewiseConstantCurrent.step` and `PiecewiseConstantCurrent.pulse` in
`thermotwin/controls.py`.

For the reference step and pulse, make a table containing:

| Time or interval | Step current | Pulse current |
| --- | ---: | ---: |
| $t<10$ s |  |  |
| $t=10$ s |  |  |
| $10<t<30$ s |  |  |
| $t=30$ s |  |  |
| $t>30$ s |  |  |

Explain what **right-continuous** means and why the values at exactly 10 s and
30 s need an explicit convention.

**My answer:**

### Exercise 2: Decode the generic representation

`PiecewiseConstantCurrent` stores `transition_times` and `values`.

1. Explain why the number of values must be one greater than the number of
   transitions.
2. Write the two tuples representing the reference pulse.
3. Predict the result of `value_at` at 9.999 s, 10 s, 29.999 s, and 30 s.
4. Explain why transition times must be finite, nonnegative, and strictly
   increasing.
5. Explain what physical ambiguity or numerical failure each validation rule
   prevents.

**My answer:**

### Exercise 3: Construct a two-pulse schedule

Without running code, construct `transition_times` and `values` for:

- baseline current 0 A;
- first 1 A pulse for $5\le t<10$ s;
- second 2 A pulse for $20\le t<24$ s;
- return to 0 A after each pulse.

Trace the current at 0, 5, 10, 15, 20, 24, and 30 s.

**My schedule and trace:**

### Checkpoint 1

Ask Codex to review Exercises 1–3 before continuing.

---

## Block 2 — Physics at a current transition

### Exercise 4: What can jump instantaneously?

At 10 s, the reference step changes current from 0 A to 1 A. Immediately
before the step, the nodes are still at 300 K.

For each quantity, state whether it is continuous or may jump at the switch and
explain why:

1. $I$
2. $T_c$ and $T_h$
3. $T_h-T_c$
4. The Peltier terms
5. The Joule term
6. $Q_c$ and $Q_h$
7. $V$
8. $VI$
9. $dT_c/dt$ and $dT_h/dt$

Use thermal capacitance in your explanation of temperature continuity.

**My answer:**

### Exercise 5: Calculate both sides of the step

Calculate the following immediately before and immediately after the 10 s
switch:

| Quantity | Just before, $I=0$ | Just after, $I=1$ A | Units |
| --- | ---: | ---: | --- |
| Cold-side Peltier term |  |  |  |
| Hot-side Peltier term |  |  |  |
| Total Joule heat |  |  |  |
| Conductive heat leak |  |  |  |
| $Q_c$ |  |  |  |
| $Q_h$ |  |  |  |
| $V$ |  |  |  |
| $VI$ |  |  |  |
| $dT_c/dt$ |  |  |  |
| $dT_h/dt$ |  |  |  |

Verify the energy identity $Q_h-Q_c=VI$ on both sides of the switch.

**My calculations:**

### Exercise 6: Compare 1 A and 2 A pulses

At $T_c=T_h=300$ K, compare the immediate effect of switching from 0 A to
either 1 A or 2 A.

1. Calculate $Q_c$, $Q_h$, $V$, $VI$, and COP for both currents.
2. Identify which contributions double and which quadruple.
3. Determine whether doubling current doubles useful cooling.
4. Explain the tradeoff between initial cooling rate and efficiency.
5. Predict which pulse deposits more total electrical energy if both last the
   same amount of time.

**My calculations and interpretation:**

### Exercise 7: What happens when the pulse turns off?

At 30 s, current returns from 1 A to 0 A, but generally $T_h>T_c$.

Without using numerical temperatures:

1. Determine which current-dependent terms become zero immediately.
2. Determine the sign of the conductive heat leak.
3. Predict the signs of $Q_c$ and $Q_h$ just after shutoff.
4. Explain the resulting heat-flow direction through the module.
5. Explain why the node temperatures remain continuous while their slopes
   change.
6. State what additional information is needed to predict the exact signs of
   both temperature rates, including reservoir effects.

**My prediction:**

### Checkpoint 2

Ask Codex to review Exercises 4–7 before continuing.

---

## Block 3 — RK4 at discontinuities

### Exercise 8: Predict the actual integration times

Suppose the reference pulse is integrated with a requested time step of 25 s.
The requested grid would cross both switches.

1. Predict every time stored in the returned trajectory from 0 through 60 s.
2. Identify which steps were shortened by a transition.
3. Identify which current applies over each integration interval.
4. Explain why the 25 s request is a maximum step rather than a promise that
   every step will have exactly that length.

**My predicted trajectory times:**

### Exercise 9: Why one current is held across each RK4 step

Read the loop in `integrate_two_node`.

1. Find where the next current transition shortens `next_time`.
2. Find where `step_current` is selected.
3. Confirm that $k_1$, $k_2$, $k_3$, and $k_4$ all use the same current within
   that interval.
4. Explain why this is correct for a piecewise-constant input when no switch
   lies inside the interval.
5. Describe the error that could occur if $k_1$ used the old current while
   $k_4$ used the new current at the end of a step crossing a switch.

**My code trace and explanation:**

### Exercise 10: State continuity versus diagnostic jumps

At a transition time, the trajectory contains one pair of temperatures, while
`evaluate_trajectory` uses the new right-continuous current.

Explain why:

1. `trajectory.cold` and `trajectory.hot` do not contain before-and-after
   temperature jumps at the same timestamp.
2. The recorded current can jump at that timestamp.
3. $Q_c$, $Q_h$, voltage, power, and COP can also jump.
4. A plotted line may visually connect samples across a jump unless the plot
   explicitly uses a step representation or duplicate boundary samples.

**My answer:**

### Exercise 11: Constant-current compatibility

Explain why these should produce identical temperature trajectories:

```python
current=1.0
```

and

```python
current=PiecewiseConstantCurrent.constant(1.0)
```

Find the test that verifies exact equality. State what kind of regression a
failure would reveal.

**My test mapping:**

### Checkpoint 3

Ask Codex to review Exercises 8–11 before continuing.

---

## Block 4 — Tests, energy, and experiment design

### Exercise 12: Explain the exact pulse-heating test

Find `test_pulse_boundaries_split_steps_and_integrate_exact_heating` in
`tests/test_transient.py`.

For that deliberately simplified model:

1. Explain why only Joule heating remains.
2. Calculate the heat rate entering each node during the pulse.
3. Calculate the expected temperature change over the pulse duration.
4. Predict the complete time and temperature tuples.
5. Explain why the requested 3 s step makes this a strong boundary-splitting
   test.
6. State which implementation errors this test would catch.

**My derivation and test explanation:**

### Exercise 13: Energy accounting over an entire pulse

For insulated nodes with no external heat inputs, add the two transient energy
balances and integrate over time. Express the change in stored node energy in
terms of the electrical power history.

Then explain how the accounting changes when reservoir heat transfer is
included. Identify every term that must be accumulated to audit energy over a
complete simulation rather than at one instant.

**My derivation:**

### Exercise 14: Design the first physical pulse experiment

Choose values for:

| Design choice | My value | Units | Reason |
| --- | ---: | --- | --- |
| Baseline current |  | A |  |
| Pulse current |  | A |  |
| Pulse start |  | s |  |
| Pulse end |  | s |  |
| Total duration |  | s |  |
| Requested integration step |  | s |  |

Before running it, state:

1. The single physical question the experiment answers.
2. The expected signs of both temperature rates before, during, and after the
   pulse.
3. Which quantities should jump at each switch.
4. Which quantities should remain continuous.
5. What result would suggest a sign error.
6. What step-size comparison will be used to check numerical convergence.

Record the finalized experiment in `05_forward_experiments.md` before running
the simulation.

**My experiment and predictions:**

### Exercise 15: Identify the current limitation

The current schedule is piecewise constant. Explain why a sine wave or smooth
ramp is not represented exactly by this API. Describe what would need to change
so RK4 could evaluate a smooth current $I(t)$ at the beginning, midpoint, and
end stage times.

State why that extension is unnecessary for rectangular step and pulse
experiments but may matter for later control optimization.

**My answer:**

### Checkpoint 4

Ask Codex to review Exercises 12–15 before implementing any new control type.

---

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
