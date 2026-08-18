# 11 — Contact reference, diagnostics, and comparison report

Status: `Not started`

## Purpose

Note 10 derives and implements the contact-aware four-node model. This sheet
studies the next layer built around that model:

1. the frozen reference experiment;
2. the trajectory and its derived histories;
3. module heat versus heat delivered through the contacts;
4. whole-system energy diagnostics;
5. comparison with the reduced two-node model;
6. the contact-resistance sweep; and
7. the code that assembles and plots the report.

Make each physical prediction before running the corresponding code. Include
units in every hand calculation. If a prediction is wrong, preserve it in the
corrections section and explain why it was wrong.

The relevant files are:

- `thermotwin/contact_experiments.py`: the experiment description and runner;
- `thermotwin/contact_diagnostics.py`: aligned derived histories;
- `thermotwin/contact_report.py`: comparison, sweep, plotting, and command-line
  entry point;
- `thermotwin/contact_transient.py`: the governing equations and RK4 solver;
- `thermotwin/experiments.py`: the reduced two-node reference;
- `tests/test_contact_experiments.py`: frozen-input and regression checks;
- `tests/test_contact_diagnostics.py`: alignment and energy checks; and
- `tests/test_contact_report.py`: sweep and PNG-report checks.

---

## Reference experiment

The contact-aware reference case uses generic, controlled values. They are not
measurements from a calibrated thermoelectric assembly.

| Quantity | Symbol | Value |
| --- | --- | ---: |
| Seebeck coefficient | $\alpha$ | 0.05 V/K |
| Electrical resistance | $R$ | 2.0 ohm |
| Module thermal conductance | $K$ | 0.5 W/K |
| Cold face capacitance | $C_c$ | 50 J/K |
| Hot face capacitance | $C_h$ | 100 J/K |
| Cold exchanger capacitance | $C_{x,c}$ | 50 J/K |
| Hot exchanger capacitance | $C_{x,h}$ | 100 J/K |
| Cold contact resistance | $R_{\mathrm{contact},c}$ | 0.25 K/W |
| Hot contact resistance | $R_{\mathrm{contact},h}$ | 0.25 K/W |
| Cold reservoir conductance | $G_c$ | 2.0 W/K |
| Hot reservoir conductance | $G_h$ | 4.0 W/K |
| Current | $I$ | 1.0 A |
| Initial temperature of every node |  | 300 K |
| Both reservoir temperatures |  | 300 K |
| Both external heat inputs |  | 0 W |
| Duration |  | 60 s |
| RK4 step |  | 0.1 s |

---

## Block 1 — Understand the experiment object

### Exercise 1: Classify the inputs

Place every quantity in the table above into one of these categories:

- thermoelectric material or module parameter;
- thermal-network parameter;
- initial condition;
- boundary condition;
- control input; or
- numerical setting.

Then answer:

1. Which values determine the governing equations?
2. Which values determine one particular experiment without changing the
   equation form?
3. Which value controls numerical resolution but is not physical?
4. Which values would have to come from measurement or calibration in a real
   digital twin?

**My classification:**

### Exercise 2: Trace the data containers

Read `FourNodeContactExperiment`, `ContactExperimentResult`, and
`FourNodeContactTemperatureTrajectory`.

1. Why is the experiment a frozen dataclass?
2. What is stored in the experiment but not in the trajectory?
3. What are the five histories in the trajectory?
4. Why does the result contain diagnostics separately from temperatures?
5. Which design lets a new diagnostic be added without changing RK4?

Draw this flow in your own words:

~~~text
experiment definition -> RK4 trajectory -> derived diagnostics -> report
~~~

**My code map:**

### Exercise 3: Count the samples before running

The duration is 60 s, the step is 0.1 s, and the initial state is included.

1. Predict the number of stored samples.
2. State the first and last time.
3. Explain why the initial sample adds one to the number of time intervals.
4. Find the test that freezes this sample count.

**My prediction:**

### Exercise 4: Explain reproducibility

The function `constant_current_contact_reference_experiment` stores all
baseline inputs in one place.

1. Why is that safer than repeating literal values in scripts and tests?
2. Which test detects an accidental change to the reference inputs?
3. Is a frozen reference necessarily a physically accurate reference?
4. What additional evidence would be needed before calling it calibrated?

**My explanation:**

### Checkpoint 1

Ask Codex to review Exercises 1–4 before evaluating the initial state.

---

## Block 2 — Predict the initial physics by hand

Use the thermoelectric equations

$$
Q_c=\alpha I T_c-\frac{1}{2}I^2R-K(T_h-T_c),
$$

$$
Q_h=\alpha I T_h+\frac{1}{2}I^2R-K(T_h-T_c),
$$

and the contact equations

$$
\dot q_{\mathrm{contact},c}
=\frac{T_{x,c}-T_c}{R_{\mathrm{contact},c}},
$$

$$
\dot q_{\mathrm{contact},h}
=\frac{T_h-T_{x,h}}{R_{\mathrm{contact},h}}.
$$

### Exercise 5: Calculate every initial heat rate

At $t=0$, calculate:

1. the cold and hot Peltier terms;
2. total Joule heating and the half assigned to each face;
3. the conductive leak;
4. $Q_c$ and $Q_h$;
5. both contact heat rates;
6. both reservoir heat rates;
7. voltage and electrical power; and
8. $Q_h-Q_c$.

Verify the units and verify $Q_h-Q_c=VI$.

**My calculations:**

### Exercise 6: Calculate all four initial temperature rates

Use

$$
C_c\dot T_c=\dot q_{\mathrm{contact},c}-Q_c,
$$

$$
C_h\dot T_h=Q_h-\dot q_{\mathrm{contact},h},
$$

$$
C_{x,c}\dot T_{x,c}
=G_c(T_{c,\infty}-T_{x,c})-
\dot q_{\mathrm{contact},c},
$$

$$
C_{x,h}\dot T_{x,h}
=G_h(T_{h,\infty}-T_{x,h})+
\dot q_{\mathrm{contact},h}.
$$

Calculate all four rates in K/s and predict which two temperatures move
immediately. Explain why the exchanger rates initially differ from the face
rates even though each face starts at the same temperature as its exchanger.

**My rate calculations:**

### Exercise 7: Predict the first contact drops

Use the signs from Exercise 6 to predict, just after $t=0$:

1. the sign of $T_{x,c}-T_c$;
2. the sign of $T_h-T_{x,h}$;
3. the sign of each contact heat rate;
4. which way energy crosses each contact; and
5. whether the face temperature span or exchanger temperature span becomes
   larger first.

**My prediction:**

### Exercise 8: Initial stored-energy check

Calculate

$$
\dot E_{\mathrm{stored}}
=C_c\dot T_c+C_h\dot T_h
+C_{x,c}\dot T_{x,c}+C_{x,h}\dot T_{x,h}.
$$

Compare it with the initial external energy rate

$$
\dot E_{\mathrm{external}}
=G_c(T_{c,\infty}-T_{x,c})
+G_h(T_{h,\infty}-T_{x,h})
+\dot q_{c,\mathrm{ext}}+\dot q_{h,\mathrm{ext}}+VI.
$$

Why do neither $Q_c$, $Q_h$, nor the contact heat rates appear separately in
the final external-energy expression?

**My energy check:**

### Checkpoint 2

Ask Codex to check the numerical values and signs in Exercises 5–8 before
running the reference experiment.

---

## Block 3 — Read and run the reference workflow

### Exercise 9: Trace the runner

Read `run_four_node_contact_experiment` without executing it.

1. Which function produces the trajectory?
2. Which function produces diagnostics?
3. Which exact experiment inputs are passed to both functions?
4. Why must diagnostics use the same current and boundary conditions as RK4?
5. What inconsistency would appear if a different current were used during
   diagnostic evaluation?

**My trace:**

### Exercise 10: Run the experiment directly

Run this from the repository root:

~~~python
from thermotwin import (
    constant_current_contact_reference_experiment,
    run_four_node_contact_experiment,
)

experiment = constant_current_contact_reference_experiment()
result = run_four_node_contact_experiment(experiment)

print(len(result.trajectory.time))
print(result.trajectory.cold_face[-1])
print(result.trajectory.hot_face[-1])
print(result.trajectory.cold_exchanger[-1])
print(result.trajectory.hot_exchanger[-1])
~~~

Record the results and compare them with Exercises 3 and 7. Do not describe a
temperature as a heat rate or a heat rate as energy.

**My results and interpretation:**

### Exercise 11: Check history alignment

For every field in `ContactTrajectoryDiagnostics`:

1. state its meaning;
2. state its units;
3. state whether it is measured directly, simulated directly, or derived;
4. verify its length equals the time-history length; and
5. explain why pointwise alignment matters when plotting or fitting data.

Which test automatically checks the lengths?

**My diagnostic table:**

### Exercise 12: Reproduce one diagnostic sample

Choose one stored time, preferably neither the first nor last. Extract its
four temperatures and current. Calculate by hand:

1. face and exchanger temperature spans;
2. both contact drops;
3. both contact heat rates;
4. $Q_c$ and $Q_h$;
5. voltage and power; and
6. both COP definitions.

Compare the hand values with the histories at the same index.

**My sample calculation:**

---

## Block 4 — Distinguish module and delivered performance

### Exercise 13: Explain why the heat rates differ

At the cold face,

$$
\dot q_{\mathrm{contact},c}-Q_c=C_c\dot T_c.
$$

At the hot face,

$$
Q_h-\dot q_{\mathrm{contact},h}=C_h\dot T_h.
$$

1. Rearrange each equation to express contact heat in terms of module heat
   and stored-energy rate.
2. Explain why $Q_c$ need not equal cold contact heat during a transient.
3. Explain why $Q_h$ need not equal hot contact heat.
4. State the steady-face condition under which each pair becomes equal.
5. Is their transient difference itself an energy loss?

**My derivation and explanation:**

### Exercise 14: Compare the two COP definitions

The diagnostics define

$$
\mathrm{COP}_{\mathrm{module}}=\frac{Q_c}{VI},
$$

$$
\mathrm{COP}_{\mathrm{exchanger}}
=\frac{\dot q_{\mathrm{contact},c}}{VI}.
$$

1. Which numerator describes the thermoelectric module face?
2. Which describes heat leaving the modeled cold exchanger through the
   contact?
3. Which is closer to the cooling service delivered to that exchanger?
4. Why can the exchanger COP initially be zero while the module COP is
   positive?
5. Why is an undefined value safer than division by zero when $VI=0$?
6. What additional definition would be needed for a time-integrated COP?

**My comparison:**

### Exercise 15: Calculate an interval performance metric

Select a time interval from the trajectory. Approximate, using a trapezoidal
sum,

$$
E_{\mathrm{cold,delivered}}
=\int \dot q_{\mathrm{contact},c}\,dt,
$$

and

$$
E_{\mathrm{electrical}}=\int VI\,dt.
$$

Calculate their ratio. Explain why averaging instantaneous COP values is not
generally equivalent to the ratio of integrated cooling to integrated input
energy.

**My calculation:**

### Checkpoint 3

Ask Codex to review Exercises 13–15 before interpreting the sweep.

---

## Block 5 — Whole-system energy diagnostics

### Exercise 16: Trace the cancellation in code

Read `evaluate_contact_trajectory`.

1. Find the calculation of all four instantaneous temperature rates.
2. Find the multiplication of each rate by its capacitance.
3. Identify every contribution to `external_rate`.
4. Explain why the residual is stored rate minus external rate.
5. Predict the residual for an exactly evaluated set of algebraic balances.

**My code trace:**

### Exercise 17: Separate algebraic closure from integrated accuracy

The energy residual is computed by evaluating the right-hand side at each
stored state.

1. What does a residual near machine precision prove?
2. Does it prove that a 0.1 s RK4 trajectory is identical to the exact ODE
   solution?
3. Which separate experiment tests time-step convergence?
4. Could an incorrect but internally self-consistent model close its energy
   balance?
5. What kinds of mistakes does energy closure catch especially well?

**My explanation:**

### Exercise 18: Construct a deliberate sign error on paper

On paper only, change the cold-exchanger contact term from negative to
positive.

1. Add all four balances again.
2. Which internal term fails to cancel?
3. What false energy source or sink appears?
4. Which existing test should fail if that error were placed in code?

Do not modify the production implementation for this exercise.

**My faulty balance and diagnosis:**

---

## Block 6 — Compare the two topologies

### Exercise 19: Make the comparison fair

Compare the frozen two-node and four-node experiments.

1. Add the cold-side face and exchanger capacitances.
2. Compare the sum with the two-node cold capacitance.
3. Repeat for the hot side.
4. Compare currents, reservoirs, reservoir conductances, initial
   temperatures, duration, and step size.
5. Explain why matching aggregate capacitance helps isolate the effect of
   topology.
6. Identify any remaining reason the trajectories need not match.

**My comparison:**

### Exercise 20: Predict the plotted temperature histories

Before generating the report, sketch or describe:

1. the cold face and cold exchanger curves;
2. the hot face and hot exchanger curves;
3. the reduced two-node cold and hot curves;
4. the face span relative to the exchanger span; and
5. which curves begin with zero slope.

Label every curve and axis with units.

**My sketch or prediction:**

### Exercise 21: State what the comparison can establish

Answer true or false and justify each answer:

1. A difference between the models proves the four-node model is more
   accurate for hardware.
2. The four-node model can represent face-to-exchanger temperature drops.
3. The two-node model is invalid for every purpose.
4. Matching aggregate capacitance makes the models mathematically identical.
5. Hardware measurements at multiple locations could help choose between the
   topologies.

**My answers:**

---

## Block 7 — Contact-resistance sweep

The report holds every reference input fixed and sets both contact
resistances to each value in

~~~text
0.1, 0.25, 0.5, 1.0 K/W.
~~~

### Exercise 22: Make four directional predictions

Before viewing the sweep, predict how increasing both contact resistances will
affect, at 60 s:

1. both contact temperature drops;
2. heat removed from the cold exchanger;
3. cold face and cold exchanger temperatures;
4. hot face and hot exchanger temperatures; and
5. disagreement with the reduced two-node result.

For each prediction, state what is held fixed. Distinguish a fixed-temperature
argument from the coupled transient result in which temperatures also change.

**My predictions:**

### Exercise 23: Trace the sweep code

Read `build_contact_comparison_report_data`.

1. Why is `dataclasses.replace` used twice?
2. Which two parameters are changed together?
3. Which values remain identical across sweep runs?
4. Which final values are stored in each `ContactResistanceSweepPoint`?
5. Why must resistance values be finite and positive?
6. What information is lost by saving only the final sweep values?

**My code trace:**

### Exercise 24: Run and interpret the report

Run:

~~~bash
python3 -m thermotwin.contact_report
~~~

For each of the four panels:

1. state the question the panel addresses;
2. identify its horizontal and vertical variables;
3. identify the physical units;
4. compare the result with your prediction; and
5. state one conclusion the panel cannot support.

Then record the maximum energy-balance residual printed by the command.

**My panel-by-panel interpretation:**

### Exercise 25: Design an asymmetric sweep

Without implementing it yet, design an experiment that varies cold contact
resistance while holding hot contact resistance fixed.

1. List the resistance values.
2. Choose the output histories or summary quantities.
3. Predict which outputs are most sensitive.
4. Explain why varying one resistance at a time helps interpretation.
5. Explain why it still may not establish parameter identifiability.

**My experiment design:**

### Checkpoint 4

Ask Codex to review Exercises 22–25 before the code-testing block.

---

## Block 8 — Understand the tests and failure modes

### Exercise 26: Map claims to tests

For each claim, find the exact test that supports it:

| Claim | Test file and test name |
| --- | --- |
| Reference inputs are frozen |  |
| Initial heat values match hand calculations |  |
| Every diagnostic history is aligned |  |
| $Q_h-Q_c=VI$ along the trajectory |  |
| Whole-system energy closes |  |
| COP is undefined at zero power |  |
| Larger swept resistance increases contact drops in this case |  |
| Larger swept resistance reduces delivered cold heat in this case |  |
| The report writer creates a valid PNG |  |

**My test map:**

### Exercise 27: Explain regression values

`test_contact_experiments.py` checks final temperatures to several decimal
places.

1. What accidental changes would these assertions catch?
2. Why do they not prove agreement with hardware?
3. How can an intentionally improved model require updating them?
4. What documentation should accompany an intentional baseline change?

**My explanation:**

### Exercise 28: Diagnose malformed data

The diagnostic evaluator rejects temperature histories with unequal lengths.

1. What could happen if `zip` silently truncated mismatched histories?
2. Why is explicit validation scientifically important?
3. Name two additional validations that may become important for real sensor
   data.

**My diagnosis:**

### Exercise 29: Run the focused tests

Run:

~~~bash
python3 -m unittest \
  tests.test_contact_transient \
  tests.test_contact_diagnostics \
  tests.test_contact_experiments \
  tests.test_contact_report
~~~

Record the number of tests, elapsed time, and result. Choose one test and
explain its physical purpose rather than merely restating its assertions.

**My test result and explanation:**

---

## Block 9 — Small coding exercises

Complete these only after understanding the existing workflow. Keep temporary
exploration outside production files unless we explicitly decide to extend
the package.

### Exercise 30: Print a compact final-state summary

Write a short script that prints, with units:

- all four final temperatures;
- both final contact drops;
- both final contact heat rates;
- final electrical power;
- both final COP values; and
- maximum absolute energy residual.

Avoid copying calculations already present in the diagnostic object.

**My script:**

### Exercise 31: Find the largest contact drop

Using the aligned histories:

1. find the index and time of the largest cold contact drop;
2. find the index and time of the largest hot contact drop;
3. print the associated temperatures and heat rates; and
4. explain whether the maximum must occur at the final time.

**My code and interpretation:**

### Exercise 32: Add a pulse-current exploration

Create a `FourNodeContactExperiment` using a pulse current already supported
by `PiecewiseConstantCurrent`.

Before running it, predict:

1. which heat terms jump at pulse start and end;
2. which temperatures remain continuous;
3. how the contact heat responds relative to the module heat; and
4. whether instantaneous and interval COP remain meaningful during all parts
   of the pulse.

Do not change the frozen reference function.

**My experiment, prediction, and result:**

### Exercise 33: Propose one report improvement

Choose one addition, such as delivered COP, energy over time, asymmetric
resistance sensitivity, or pulse response.

Specify:

1. the scientific question;
2. the required data;
3. where that data already exists or must be added;
4. the appropriate plot; and
5. one automated test.

Do not implement it until the scientific purpose is clear.

**My proposal:**

---

## Interview teach-back

### 30-second explanation

What does the frozen contact reference add beyond the four-node equations?

**My answer:**

### Two-minute explanation

Explain the path from experiment configuration to RK4 trajectory, derived
diagnostics, energy closure, topology comparison, and resistance sweep.
Clearly distinguish module cooling from exchanger-delivered cooling.

**My answer:**

### Challenge questions

1. Why can module COP exceed exchanger-delivered COP during this transient?
2. Why is contact heat internal in the whole-system energy balance?
3. What does machine-precision algebraic energy closure prove and not prove?
4. Why does the resistance sweep show sensitivity but not identifiability?
5. Why is the two-node comparison useful even though it is not hardware
   validation?
6. Why should the reference experiment remain unchanged while exploratory
   experiments use copied or replaced configurations?
7. Which part of the workflow will change when measured data are introduced?

**My answers:**

---

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

| Original claim or calculation | Exact error | Consequence | Corrected reasoning |
| --- | --- | --- | --- |
|  |  |  |  |
