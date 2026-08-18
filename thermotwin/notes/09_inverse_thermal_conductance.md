# 09 — Inverse thermal conductance

Status: `Not started`

## Learning objectives

By the end of these exercises, I should be able to:

1. Explain how an inverse PINN differs from both RK4 and the forward PINN.
2. Identify which quantities are known, observed, predicted, and inferred.
3. Explain how the module thermal conductance $K$ affects both node balances.
4. Explain why a temperature difference is required to learn $K$.
5. Trace how sparse RK4 temperatures are turned into synthetic observations.
6. Explain why the network weights and $K$ must be optimized jointly.
7. Derive the dimensionless physics and observation losses.
8. Explain the purpose and limitations of the softplus parameterization.
9. Distinguish observation fit, dense-trajectory prediction, and parameter
   recovery.
10. Identify what this noise-free single-parameter result does and does not
    establish.

Work through one block at a time. Make predictions before running training.
Include units whenever a quantity has units. Record incorrect reasoning in the
corrections section instead of deleting it.

## Reference inverse problem

The first inverse problem uses the same 60 s constant-current experiment as the
forward PINN. The RK4 solver generates synthetic truth.

The experiment configuration still stores the true $K$ so RK4 can generate the
synthetic observations. During inverse training, `physics_residuals` receives
the model's learned conductance as an explicit override, so the stored true
value does not enter the training residual.

| Quantity | Value | Units or role |
| --- | ---: | --- |
| True $\alpha$ | 0.05 | V/K; known |
| True $R$ | 2.0 | ohm; known |
| True $K$ | 0.5 | W/K; hidden from training |
| Initial guess for $K$ | 0.2 | W/K; trainable starting value |
| $C_c$ | 100 | J/K; known |
| $C_h$ | 200 | J/K; known |
| $G_c$ | 2.0 | W/K; known |
| $G_h$ | 4.0 | W/K; known |
| Current | 1.0 | A; known and constant |
| Initial temperatures | 300, 300 | K; known exactly |
| Observation interval | 5 | s |
| Observation times | 0, 5, ..., 60 | s |
| Paired observations | 13 | $T_c$ and $T_h$ at each time |
| Collocation points | 128 | physics locations |
| Dense validation step | 0.1 | s; not used in the loss |

The relevant files are:

- `thermotwin/inverse_thermal_conductance.py`: observations, inverse model,
  loss, training, validation, and command-line workflow;
- `thermotwin/forward_pinn.py`: temperature network and physics residuals;
- `thermotwin/experiments.py`: the reference experiment and RK4 execution;
- `tests/test_inverse_thermal_conductance.py`: positivity, sensitivity,
  identifiability, and recovery checks; and
- `thermotwin/README_detailed.md`: the complete current implementation guide.

---

## Block 1 — Define the inverse problem precisely

### Exercise 1: Compare all three solvers

Compare the conventional RK4 solver, forward PINN, and inverse PINN.

For each method, state:

1. What it receives as input.
2. Which physical parameters are assumed known.
3. What it calculates or learns.
4. Whether it uses measured or synthetic temperature observations.
5. How the governing equations enter the method.
6. What independent information is used for validation.

Complete the table before reading the implementations in detail:

| Question | RK4 | Forward PINN | Inverse PINN |
| --- | --- | --- | --- |
| Temperature representation |  |  |  |
| Is $K$ known? |  |  |  |
| Uses observations in training? |  |  |  |
| Uses physics residuals? |  |  |  |
| Main validation target |  |  |  |

**My explanation:**

### Exercise 2: Classify every quantity

Sort each item into **known physical parameter**, **known experimental input**,
**observed data**, **network-predicted state**, **inferred parameter**,
**training setting**, or **validation-only truth**:

- time;
- $T_c(t)$ and $T_h(t)$;
- the 13 observed cold temperatures;
- the 13 observed hot temperatures;
- the dense RK4 temperature trajectory;
- $\alpha$;
- $R$;
- $K$;
- $C_c$ and $C_h$;
- $G_c$ and $G_h$;
- current;
- reservoir temperatures;
- initial temperatures;
- hidden width;
- collocation-point count;
- learning rates; and
- random seed.

Then answer:

1. Why must the true value $K=0.5$ W/K remain outside the training loss?
2. Would comparing the final estimate to the true value during every epoch
   constitute information leakage?
3. Which of these categories would change when real hardware replaces the
   synthetic experiment?

**My classification and explanation:**

### Exercise 3: State the scientific question

Write the current inverse problem as one precise scientific question. It
should identify:

1. The one unknown parameter.
2. The available measurements.
3. The known inputs and parameters.
4. The physical constraints.
5. The experiment duration and sampling interval.
6. The numerical success criterion.

Then explain why the current result is a controlled baseline rather than a
realistic parameter-identification study.

**My scientific question:**

### Checkpoint 1

Ask Codex to review Exercises 1–3 before deriving the sensitivity to $K$.

---

## Block 2 — How $K$ affects the physics

### Exercise 4: Locate $K$ in both heat rates

Start with

$$
Q_c=\alpha I T_c-\frac{1}{2}I^2R-K(T_h-T_c),
$$

$$
Q_h=\alpha I T_h+\frac{1}{2}I^2R-K(T_h-T_c).
$$

Assume $T_h>T_c$ and hold both temperatures and the current fixed.

1. Calculate $\partial Q_c/\partial K$.
2. Calculate $\partial Q_h/\partial K$.
3. State their units.
4. Predict how increasing $K$ changes $Q_c$ and $Q_h$.
5. Explain the physical meaning of the change.
6. Does a larger $K$ represent better heat pumping or a larger parasitic heat
   leak?

**My derivatives and interpretation:**

### Exercise 5: Propagate the effect into temperature rates

Use the node balances

$$
C_c\frac{dT_c}{dt}
=G_c(T_{c,\infty}-T_c)+\dot q_{c,\mathrm{ext}}-Q_c,
$$

$$
C_h\frac{dT_h}{dt}
=G_h(T_{h,\infty}-T_h)+\dot q_{h,\mathrm{ext}}+Q_h.
$$

At fixed $T_c$, $T_h$, and $I$, derive:

$$
\frac{\partial}{\partial K}\left(\frac{dT_c}{dt}\right)
$$

and

$$
\frac{\partial}{\partial K}\left(\frac{dT_h}{dt}\right).
$$

Then answer:

1. Which temperature rate increases when $K$ increases?
2. Which temperature rate decreases?
3. Why does a stronger hot-to-cold leak tend to reduce the separation between
   $T_h$ and $T_c$?
4. How do the capacitances affect the magnitude of this sensitivity?
5. Why does the corresponding unit test hold the candidate temperature path
   fixed while changing only $K$?

**My derivation and prediction:**

### Exercise 6: Connect physical rates to residual signs

The PINN residuals are

$$
r_c=\left(\frac{dT_c}{dt}\right)_{\mathrm{network}}
-\left(\frac{dT_c}{dt}\right)_{\mathrm{physics}},
$$

$$
r_h=\left(\frac{dT_h}{dt}\right)_{\mathrm{network}}
-\left(\frac{dT_h}{dt}\right)_{\mathrm{physics}}.
$$

Suppose the candidate path is fixed at $T_c=295$ K and $T_h=305$ K with zero
network derivatives. Compare $K=0.5$ W/K with $K=1.0$ W/K.

Before evaluating the test, predict whether each residual becomes larger or
smaller as $K$ increases. Then locate
`test_larger_k_changes_fixed_path_residuals_in_expected_directions` and check
your prediction.

Explain why a residual-direction test can reveal a sign mistake even without
knowing the exact trained trajectory.

**My prediction and test explanation:**

### Exercise 7: Prove the uninformative limiting case

Set $I=0$ and suppose

$$
T_c(t)=T_h(t)=300\ \mathrm{K}
$$

for the entire experiment.

1. Evaluate $K(T_h-T_c)$ for an arbitrary positive $K$.
2. Evaluate both node residuals.
3. Calculate the derivative of the physics loss with respect to $K$.
4. Explain why every value of $K$ is observationally equivalent in this
   experiment.
5. Explain why a longer version of the same equilibrium experiment would not
   fix the problem.
6. Explain why more precise sensors would not fix it either.
7. Find the unit test that checks the zero gradient.

**My derivation and explanation:**

### Exercise 8: Structural versus practical identifiability

Compare these two cases:

1. $T_h-T_c=0$ exactly for all time.
2. $T_h-T_c$ becomes nonzero but remains much smaller than the temperature
   sensor noise.

For each case, state whether the difficulty is best described as structural
non-identifiability or practical non-identifiability. Explain what change to
the experiment might help and what change would not help.

**My comparison:**

### Checkpoint 2

Ask Codex to review Exercises 4–8 before examining the observation generator.

---

## Block 3 — Synthetic observations and data separation

### Exercise 9: Count the observations by hand

For a 60 s experiment, calculate the observation times and the number of
paired observations for each interval:

| Interval | Observation times | Number of pairs |
| ---: | --- | ---: |
| 2.5 s |  |  |
| 5 s |  |  |
| 10 s |  |  |
| 15 s |  |  |
| 20 s |  |  |

Remember that both $t=0$ and $t=60$ are included. Explain why one paired
observation contains two scalar temperature values.

**My calculations:**

### Exercise 10: Trace `synthetic_temperature_observations`

Read the function from top to bottom.

1. Which function produces the clean trajectory?
2. Why must the interval be finite and positive?
3. How is the final time included when the interval does not divide the
   duration exactly?
4. Why does the helper interpolate rather than assume every requested
   observation time is an RK4 output time?
5. What does `TemperatureObservations` validate?
6. Why must observation times increase strictly?
7. What kinds of sensor behavior are deliberately absent from this function?

**My code trace:**

### Exercise 11: Separate training data from validation data

Draw the data flow from the reference experiment to the final metrics:

```text
reference experiment
    -> RK4 trajectory
        -> sparse observations -> training loss
        -> dense trajectory -----------------> final validation
```

Then answer:

1. Why is the dense trajectory not passed to the training function?
2. Why are observation RMSE and dense-trajectory RMSE separate metrics?
3. Can a model match all 13 observation times but be inaccurate between them?
4. Does dense validation here test generalization to a new operating
   condition?
5. What additional split would be needed to test operating-regime
   generalization?

**My explanation:**

### Exercise 12: Predict the effect of observation spacing

Before running anything, predict how changing the interval from 5 s to 20 s
might affect:

- inferred $K$;
- observation RMSE;
- dense-trajectory RMSE;
- run time; and
- variability across random seeds.

Do not assume that four observation pairs must fail. State which result would
support the prediction and which would contradict it.

Run one interval at a time with:

```bash
python3 -m thermotwin.inverse_thermal_conductance \
  --observation-interval 5
```

Record the result before changing the interval:

| Interval | Pairs | Inferred $K$ | Parameter error | Cold dense RMSE | Hot dense RMSE |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 s |  |  |  |  |  |
| 10 s |  |  |  |  |  |
| 15 s |  |  |  |  |  |
| 20 s |  |  |  |  |  |

Explain why one training run per interval is not enough for a strong
identifiability conclusion.

**My prediction, results, and interpretation:**

### Checkpoint 3

Ask Codex to review Exercises 9–12 before tracing the inverse network.

---

## Block 4 — Positive parameterization and gradient flow

### Exercise 13: Explain the softplus transform

The optimizer does not update $K$ directly. It updates
$k_{\mathrm{raw}}$, while the physical value is

$$
K=\mathrm{softplus}(k_{\mathrm{raw}})
=\log(1+e^{k_{\mathrm{raw}}}).
$$

1. Show that $K>0$ for every finite $k_{\mathrm{raw}}$.
2. Calculate the limiting behavior as $k_{\mathrm{raw}}\to-\infty$.
3. Calculate the limiting behavior as $k_{\mathrm{raw}}\to+\infty$.
4. Explain why unconstrained optimization directly on $K$ could produce an
   unphysical value.
5. Explain why softplus is smoother than clipping a negative value to zero.
6. Does this constraint prove that the inferred $K$ is correct?
7. Does it make an unidentifiable experiment informative?

**My derivation and explanation:**

### Exercise 14: Verify the physical initial guess

`_inverse_softplus` converts a requested physical starting value into a raw
value. The model then applies softplus to recover the physical value.

1. Explain why this inverse conversion is needed.
2. What initial physical $K$ would result if the code simply stored
   `raw_thermal_conductance = 0.2`?
3. Find the test that confirms the model starts at 0.2 W/K.
4. Why does the same test also inspect the temperatures at $t=0$?
5. Which invalid initial guesses does `_inverse_softplus` reject?

**My code trace and calculation:**

### Exercise 15: Trace the gradient from loss to $K$

Write a chain-rule path showing how the total loss changes
$k_{\mathrm{raw}}$:

```text
total loss
    <- residuals and observation errors
    <- predicted temperatures and physical rates
    <- K
    <- softplus(raw K)
```

Then answer:

1. Which loss component depends explicitly on $K$ through the equations?
2. Does the observation loss contain $K$ as a written algebraic term?
3. How can observation error still influence the final value of $K$ during
   joint optimization?
4. What is $dK/dk_{\mathrm{raw}}$?
5. Why does `create_graph=True` remain important?
6. What does a zero gradient with respect to raw $K$ mean in the equilibrium
   limiting-case test?
7. Find the learned-conductance override passed to `physics_residuals` and
   explain how it prevents the stored synthetic truth from entering the
   training residual.

**My gradient explanation:**

### Exercise 16: Distinguish the two parameter groups

Read the Adam optimizer construction in
`train_inverse_thermal_conductance`.

1. Which parameters use the network learning rate?
2. Which parameter uses the parameter learning rate?
3. What are the two default rates?
4. Why might the best rate for thousands of network weights differ from the
   best rate for one raw physical parameter?
5. Predict the failure mode if the $K$ learning rate is much too small.
6. Predict the failure mode if it is much too large.
7. Explain why changing both rates simultaneously would make an experiment
   difficult to interpret.

**My code trace and predictions:**

### Checkpoint 4

Ask Codex to review Exercises 13–16 before analyzing the loss.

---

## Block 5 — Physics loss, observation loss, and joint training

### Exercise 17: Derive the dimensionless losses

The physics loss is

$$
\mathcal L_{\mathrm{physics}}
=\mathrm{mean}\left[\left(\frac{r_c}{s_r}\right)^2\right]
+\mathrm{mean}\left[\left(\frac{r_h}{s_r}\right)^2\right],
$$

where $s_r=0.1$ K/s. The observation loss is

$$
\mathcal L_{\mathrm{obs}}
=\mathrm{mean}\left[
\left(\frac{T_{\mathrm{network}}-T_{\mathrm{observed}}}{s_T}\right)^2
\right],
$$

where $s_T=1$ K.

1. Show that both losses are dimensionless.
2. Explain why the cold and hot physics terms are averaged separately and
   then added.
3. Over how many scalar errors is the observation mean calculated for 13
   paired observations?
4. What numerical role do $s_r$ and $s_T$ play?
5. Are they new physical constants?
6. How would halving $s_r$ change the numerical physics loss for unchanged
   residuals?
7. Why can scaling change optimization even though it does not change the
   governing equations?

**My derivation and explanation:**

### Exercise 18: Explain why both loss components are necessary

Consider two hypothetical training runs.

#### Case A: observation loss only

1. Could the network interpolate all 13 temperature pairs without satisfying
   the ODEs between them?
2. What would constrain $K$?
3. Why could an apparently excellent observation fit be physically
   meaningless?

#### Case B: physics loss only

1. For a chosen positive $K$, can the network learn the valid trajectory for
   that $K$?
2. Could a different $K$ also have its own physically valid trajectory?
3. What information selects the synthetic truth $K=0.5$ W/K?

Explain how the joint loss makes the model find a trajectory that is both
physically admissible and compatible with the sparse observations.

**My comparison:**

### Exercise 19: Trace one inverse-training epoch

Put these operations in order:

- clear old gradients;
- predict temperatures at collocation times;
- compute residuals using the current learned $K$;
- normalize, square, and average both residuals;
- predict temperatures at observation times;
- calculate the normalized observation error;
- combine weighted losses;
- backpropagate through network weights and raw $K$;
- update both optimizer parameter groups; and
- record losses and the physical conductance.

Identify which operations occur once before the epoch loop and which occur
inside every epoch. Explain why the observation and collocation times are
different tensors.

**My ordered trace:**

### Exercise 20: Analyze loss weights without guessing

The total loss is

$$
\mathcal L
=w_p\mathcal L_{\mathrm{physics}}
+w_o\mathcal L_{\mathrm{obs}}.
$$

The baseline uses $w_p=w_o=1$.

For each change, predict a possible benefit and a possible failure mode:

1. $w_p\gg w_o$.
2. $w_o\gg w_p$.
3. Changing a weight while also changing its normalization scale.
4. Selecting weights only because they produce the desired value of $K$.

Explain what diagnostics should be inspected before concluding that one set of
weights is better.

**My predictions:**

### Checkpoint 5

Ask Codex to review Exercises 17–20 before running the baseline.

---

## Block 6 — Baseline execution and validation

### Exercise 21: Predict and run the baseline

Before running training, predict:

1. Whether $K$ should move upward or downward from 0.2 W/K.
2. Whether $T_h-T_c$ should be larger for $K=0.2$ or $K=0.5$ under otherwise
   identical conditions.
3. Whether observation RMSE must be smaller than dense-trajectory RMSE.
4. Whether low final loss guarantees exact parameter recovery.

Run:

```bash
python3 -m thermotwin.inverse_thermal_conductance
```

Record:

| Quantity | Result | Units |
| --- | ---: | --- |
| Device |  | — |
| Observation pairs |  | — |
| Initial $K$ |  | W/K |
| True $K$ |  | W/K |
| Inferred $K$ |  | W/K |
| Relative parameter error |  | % |
| Final normalized physics loss |  | dimensionless |
| Final normalized observation loss |  | dimensionless |
| Cold dense-trajectory RMSE |  | K |
| Hot dense-trajectory RMSE |  | K |
| Cold observation RMSE |  | K |
| Hot observation RMSE |  | K |

Explain whether each prediction was supported.

**My prediction, results, and interpretation:**

### Exercise 22: Distinguish all validation metrics

Explain what each metric can reveal and what it cannot prove:

1. Absolute error in $K$.
2. Relative error in $K$.
3. Observation RMSE.
4. Dense-trajectory RMSE.
5. Final physics loss.
6. Final observation loss.

Then construct a plausible case with:

- low observation RMSE but wrong $K$; and
- correct $K$ but unacceptable temperature prediction.

What additional diagnostic would you inspect in each case?

**My metric interpretation:**

### Exercise 23: Initial-guess experiment

Keep the data, architecture, loss, seed, and epoch count fixed. Change only the
initial physical conductance:

```bash
python3 -m thermotwin.inverse_thermal_conductance --initial-k 0.1
python3 -m thermotwin.inverse_thermal_conductance --initial-k 0.2
python3 -m thermotwin.inverse_thermal_conductance --initial-k 1.0
```

Before running, predict whether all three estimates will converge to the same
value. Record:

| Initial $K$ | Final $K$ | Parameter error | Physics loss | Observation loss |
| ---: | ---: | ---: | ---: | ---: |
| 0.1 W/K |  |  |  |  |
| 0.2 W/K |  |  |  |  |
| 1.0 W/K |  |  |  |  |

Explain what agreement would suggest and what disagreement would suggest.
State why three successful starts still would not prove global uniqueness.

**My prediction and results:**

### Exercise 24: Map every inverse unit test

For each test in `tests/test_inverse_thermal_conductance.py`, write:

1. The physical or numerical claim being tested.
2. The failure it would catch.
3. Whether it is a unit, limiting-case, integration, or training test.

| Test | Claim | Likely failure caught | Test category |
| --- | --- | --- | --- |
| Synthetic observation sampling |  |  |  |
| Positive $K$ and exact initial state |  |  |  |
| Residual direction when $K$ increases |  |  |  |
| Zero-gradient unidentifiability |  |  |  |
| CPU recovery from sparse data |  |  |  |

Which test is most directly about physics? Which is most expensive? Which one
would fail if the optimizer no longer updated raw $K$?

**My test map:**

### Checkpoint 6

Ask Codex to review Exercises 21–24 before interpreting the scientific scope.

---

## Block 7 — Scientific interpretation and limitations

### Exercise 25: Explain what the baseline establishes

Write separate explanations for each supported claim:

1. The observation generator samples the intended RK4 experiment.
2. The inverse parameter remains physically positive.
3. The residual equations respond to $K$ with the intended signs.
4. The experiment contains information about $K$ once a temperature
   separation develops.
5. Joint optimization can recover the synthetic value in one controlled
   noise-free case.
6. The learned trajectory agrees with the conventional solver between the
   observation times.

Then explain why none of these claims alone establishes hardware accuracy.

**My supported-claims explanation:**

### Exercise 26: List what the baseline does not establish

For every item, explain what new experiment or implementation would be needed:

1. Robustness to random sensor noise.
2. Robustness to calibration bias.
3. Robustness to sensor time lag.
4. Recovery from only one temperature sensor.
5. Recovery of multiple parameters simultaneously.
6. Generalization to a withheld current or thermal load.
7. Uncertainty or confidence intervals on $K$.
8. Distinguishing module conductance from contact resistance.
9. Agreement with real hardware.
10. Validity when properties depend on temperature.

**My limitation analysis:**

### Exercise 27: Do not confuse $K$ with contact resistance

The inferred parameter is the module's effective parasitic thermal
conductance:

$$
\dot Q_{\mathrm{leak}}=K(T_h-T_c).
$$

An explicit thermal contact resistance would instead describe a temperature
drop between two different nodes, such as a thermoelectric face and a heat
exchanger:

$$
\dot Q_{\mathrm{contact}}
=\frac{T_{\mathrm{face}}-T_{\mathrm{exchanger}}}{R_{\mathrm{contact}}}.
$$

1. Compare the units of $K$ and $R_{\mathrm{contact}}$.
2. Explain why they are not interchangeable.
3. Identify the additional temperatures required to model the contact
   explicitly.
4. Explain how a fitted effective $K$ could absorb some unmodeled behavior
   without making contact resistance identifiable.
5. Explain why the present inverse result does not complete the roadmap goal
   of inferring contact resistance.

**My comparison:**

### Exercise 28: Design the first stronger inverse study

Choose exactly one extension:

- vary observation spacing across repeated random seeds;
- add controlled Gaussian temperature noise;
- compare several initial guesses systematically;
- fit a withheld constant-current experiment; or
- compare the inverse PINN with nonlinear least squares.

Write:

1. One scientific question.
2. One independent variable.
3. The controlled variables.
4. A prediction made before execution.
5. The required repetitions.
6. The validation metrics.
7. A limiting-case or failure check.
8. A success criterion that does not depend on seeing the desired answer.

**My proposed study:**

---

## Interview teach-back

Answer each question without reading the code.

### 30-second explanation

What inverse problem did we solve, what information did the model receive, and
what did it recover?

**My answer:**

### Two-minute explanation

Explain:

1. The role of sparse observations.
2. The role of collocation points.
3. How $K$ enters the physics.
4. Why softplus is used.
5. How the result is validated.
6. The most important limitation.

**My answer:**

### Challenge questions

1. Why use a PINN instead of fitting $K$ with the RK4 solver and nonlinear
   least squares?
2. How do you know the recovered parameter is unique?
3. Why is a low trajectory error not proof of correct parameter recovery?
4. What happens if the experiment never produces $T_h\ne T_c$?
5. How would measurement noise change the inference problem?
6. Why infer $K$ before attempting several parameters at once?
7. What experiment would you run next to obtain more information about $K$?
8. Why is the inferred $K$ not an estimate of contact resistance?

**My answers:**

---

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
