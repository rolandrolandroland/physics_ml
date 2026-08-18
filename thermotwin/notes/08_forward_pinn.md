# 08 — Forward PINN

Status: `Not started`

## Learning objectives

By the end of these exercises, I should be able to:

1. Explain how the forward PINN differs from the conventional RK4 solver.
2. Identify which quantities the network predicts and which remain fixed.
3. Derive both physics residuals from the two-node energy balances.
4. Explain how automatic differentiation provides temperature derivatives.
5. Explain why the implemented output satisfies both initial conditions
   exactly.
6. Distinguish physics loss, trajectory error, and hardware accuracy.
7. Trace the complete path from experiment definition through training and
   validation.
8. Identify the limitations of this first constant-current PINN.

Work through one block at a time. Make predictions before running code. Include
units when discussing physical quantities, and record mistakes in the
corrections section rather than erasing the original reasoning.

## Reference forward problem

The first PINN uses the same reference experiment as the conventional solver:

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
| $I$ | 1.0 | A |
| Both external heat inputs | 0 | W |
| Duration | 60 | s |
| RK4 reference step | 0.1 | s |

The relevant files are:

- `thermotwin/experiments.py`: experiment inputs and conventional execution;
- `thermotwin/forward_pinn.py`: network, residuals, training, prediction, and
  validation;
- `tests/test_experiments.py`: frozen reference checks; and
- `tests/test_forward_pinn.py`: PINN sign, limiting-case, and training checks.

---

## Block 1 — What problem is the PINN solving?

### Exercise 1: Compare RK4 and the forward PINN

In my own words, compare `integrate_two_node` and `ForwardPINN`.

Address all of the following:

1. What each one receives as input.
2. What each one returns as output.
3. How RK4 advances from one time to the next.
4. How the PINN can evaluate a requested time without marching through every
   earlier time.
5. Where the physical equations enter each method.
6. Whether either method changes the physical assumptions.

**My answer:**

### Exercise 2: Separate learned and fixed quantities

For the first forward PINN, sort the following into **network input**,
**network output**, **fixed physical parameter**, **fixed experimental input**,
or **training setting**:

- time;
- $T_c$ and $T_h$;
- $\alpha$, $R$, and $K$;
- $C_c$, $C_h$, $G_c$, and $G_h$;
- current;
- reservoir temperatures;
- external heat inputs;
- number of hidden layers;
- hidden width;
- number of collocation points;
- learning rate; and
- number of epochs.

Then explain why this is a **forward** problem rather than an inverse parameter
inference problem.

**My classification and explanation:**

### Exercise 3: Explain the role of the reference experiment

Read `TwoNodeExperiment`, `constant_current_reference_experiment`, and
`run_two_node_experiment` in `thermotwin/experiments.py`.

1. Why are all experiment inputs stored together?
2. What error could occur if the PINN and RK4 runs silently used different
   parameter values or initial conditions?
3. Which object contains temperatures and which object contains $Q_c$, $Q_h$,
   voltage, power, and COP?
4. Why is it important that the RK4 temperatures are not used in the PINN
   training loss?
5. What exactly does comparison with RK4 validate, and what does it not
   validate?

**My answer:**

### Checkpoint 1

Ask Codex to review Exercises 1–3 before deriving the residuals.

---

## Block 2 — Physics residuals and signs

### Exercise 4: Derive the cold residual

Start with the agreed cold-node balance:

$$
C_c\frac{dT_c}{dt}
=G_c(T_{c,\infty}-T_c)+\dot q_{c,\mathrm{ext}}-Q_c.
$$

Use

$$
Q_c=\alpha I T_c-\frac{1}{2}I^2R-K(T_h-T_c)
$$

to write an expression for $dT_c/dt$. Then define the PINN cold residual as

$$
r_c=\left(\frac{dT_c}{dt}\right)_{\mathrm{network}}
-\left(\frac{dT_c}{dt}\right)_{\mathrm{physics}}.
$$

1. Write the fully expanded expression for $r_c$.
2. Show by units that every term in $r_c$ has units of K/s.
3. Explain why $Q_c$ appears with a minus sign in the cold balance.
4. State what $r_c=0$ means physically.

**My derivation and unit check:**

### Exercise 5: Derive the hot residual

Repeat Exercise 4 using

$$
C_h\frac{dT_h}{dt}
=G_h(T_{h,\infty}-T_h)+\dot q_{h,\mathrm{ext}}+Q_h
$$

and

$$
Q_h=\alpha I T_h+\frac{1}{2}I^2R-K(T_h-T_c).
$$

1. Write the fully expanded expression for $r_h$.
2. Explain why $Q_h$ appears with a plus sign in the hot balance.
3. Show that $r_h$ has units of K/s.
4. Explain why the cold and hot residuals must both be small.

**My derivation and unit check:**

### Exercise 6: Reproduce the initial residual test

At $t=0$, the reference problem has $T_c=T_h=300$ K and $I=1$ A.

1. Recalculate $Q_c$, $Q_h$, $dT_c/dt$, and $dT_h/dt$.
2. Consider the candidate functions

   $$
   T_c(t)=300-0.14t,
   $$

   $$
   T_h(t)=300+0.08t.
   $$

3. Evaluate $r_c$ and $r_h$ at $t=0$.
4. Explain why these linear functions satisfy the equations at $t=0$ but are
   not expected to be the exact solution for the entire 60 s interval.
5. Find the unit test that implements this check.

**My calculation and explanation:**

### Exercise 7: Zero-current equilibrium limiting case

Set $I=0$ and suppose the network predicts $T_c=T_h=300$ K for every time.

1. Evaluate the Peltier, Joule, and conductive terms.
2. Evaluate both reservoir heat-transfer terms.
3. Evaluate both predicted temperature derivatives.
4. Show that $r_c=r_h=0$ for every time.
5. Explain why this is a stronger sign check than testing only one time.
6. Find the corresponding unit test.

**My derivation and test mapping:**

### Exercise 8: Predict consequences of common equation errors

For each hypothetical bug, predict the qualitative effect on the learned
trajectory and state which test or comparison might detect it:

1. Use $+Q_c$ instead of $-Q_c$ in the cold balance.
2. Use $-Q_h$ instead of $+Q_h$ in the hot balance.
3. Omit the factor of $1/2$ from each face's Joule term.
4. Replace $T_c$ with $T_h$ in the cold Peltier term.
5. Divide the cold balance by $C_h$ instead of $C_c$.
6. Use temperatures in degrees Celsius inside $\alpha I T$.

**My predictions:**

### Checkpoint 2

Ask Codex to review Exercises 4–8 before tracing the neural-network code.

---

## Block 3 — Network and automatic differentiation

### Exercise 9: Trace the network architecture

Read `ForwardPINN.__init__` and `ForwardPINN.forward`.

1. What is the dimension of the network input?
2. What is the dimension of the raw network output?
3. What activation function is used, and why is a smooth activation useful
   when time derivatives are required?
4. For two hidden layers of width 32, write the sequence of layer dimensions.
5. Count the total trainable weights and biases.
6. Explain why the fixed physical parameters are not trainable in this first
   model.

**My code trace and parameter count:**

### Exercise 10: Time normalization

The network uses

$$
\tau=2\frac{t}{t_{\mathrm{end}}}-1.
$$

1. Calculate $\tau$ at 0, 15, 30, 45, and 60 s.
2. Explain why presenting values roughly between $-1$ and $1$ is usually
   easier for a neural network than presenting raw times from 0 to 60.
3. Does normalization change the physical time derivative computed by
   automatic differentiation? Explain how the chain rule enters.
4. Predict what could go wrong if the code differentiated with respect to
   $\tau$ but treated the result as $dT/dt$ without the conversion factor.

**My calculations and explanation:**

### Exercise 11: Exact initial-condition transform

The implemented temperatures have the form

$$
T(t)=T(0)+\frac{t}{t_{\mathrm{end}}}T_{\mathrm{scale}}N(t),
$$

where $N(t)$ is the raw network output.

1. Substitute $t=0$ and prove that the initial condition is exact for any
   network weights.
2. Differentiate the expression with respect to time.
3. Explain why enforcing $T(0)$ does not force the initial derivative to zero.
4. What would happen if the multiplier $t/t_{\mathrm{end}}$ were omitted?
5. Compare this hard constraint with adding an initial-condition penalty to
   the loss.
6. Explain the numerical purpose of `temperature_scale` and whether it is a
   new physical parameter.

**My derivation and explanation:**

### Exercise 12: Trace automatic differentiation

Read `physics_residuals` and answer:

1. Why must the time tensor have `requires_grad=True`?
2. What do the two calls to `torch.autograd.grad` calculate?
3. Why is `create_graph=True` needed during training?
4. Why would calling `.detach()` on the predicted temperatures before taking
   derivatives break the physics loss?
5. Why do the derivatives have one value per collocation point?
6. Where do the agreed $Q_c$ and $Q_h$ equations appear in tensor form?

**My code trace:**

### Exercise 13: Collocation points and loss

The training loss is

$$
\mathcal L
=\operatorname{mean}(r_c^2)+\operatorname{mean}(r_h^2).
$$

1. Why are the residuals squared?
2. Why is a mean used rather than a sum?
3. What units does each squared residual have?
4. What is a collocation point, and why does it not require a measured
   temperature label?
5. Explain why a network could satisfy the residual at a small number of
   points but behave poorly between them.
6. Predict the tradeoff when increasing the number of collocation points.
7. Explain why both residual terms are included in one loss.

**My answer:**

### Checkpoint 3

Ask Codex to review Exercises 9–13 before running training experiments.

---

## Block 4 — Training, validation, and interpretation

### Exercise 14: Run and record the baseline

Before running the model, predict the signs of the final changes in $T_c$ and
$T_h$. Then run:

```bash
python3 -m thermotwin.forward_pinn
```

Record:

| Quantity | Result | Units |
| --- | ---: | --- |
| Device |  | — |
| Initial physics loss |  | K$^2$/s$^2$ |
| Final physics loss |  | K$^2$/s$^2$ |
| Cold RMSE against RK4 |  | K |
| Hot RMSE against RK4 |  | K |

Then answer:

1. By what factor did the physics loss decrease?
2. Are the RMSE values small relative to the total temperature changes?
3. Does this prove that the physical model matches a real thermoelectric
   system? Why or why not?
4. Why is RK4 comparison still useful even though it is not hardware
   validation?

Generate the full comparison report with:

```bash
python3 -m thermotwin.forward_pinn_report \
  --output forward_pinn_comparison.png
```

Inspect all four panels. Identify where the largest temperature error occurs,
where the largest residual occurs, and whether the loss curve is still
decreasing at the final epoch. Explain what each panel reveals that the scalar
RMSE values alone do not reveal.

**My prediction, results, and interpretation:**

### Exercise 15: Trace one training epoch

Read `train_forward_pinn` and put these operations in order:

- evaluate the network;
- create the fixed collocation-time tensor;
- calculate both physics residuals;
- clear old parameter gradients;
- square and average residuals;
- backpropagate through the residual calculation;
- update weights with Adam; and
- save the scalar loss.

Explain the purpose of `zero_grad`, `backward`, and `step`. Identify which
operation changes the network parameters.

**My ordered trace:**

### Exercise 16: One-variable-at-a-time training experiment

Choose exactly one training setting to change: epochs, collocation points,
hidden width, hidden layers, learning rate, or random seed. Keep every physical
input fixed.

Before running, predict how the change may affect runtime, final physics loss,
and RK4 error. Record at least three values:

| Changed setting | Runtime | Final physics loss | Cold RMSE | Hot RMSE |
| ---: | ---: | ---: | ---: | ---: |
|  |  |  |  |  |
|  |  |  |  |  |
|  |  |  |  |  |

Explain whether the results support the prediction. Do not change multiple
settings at once, because that would make the cause of any difference unclear.

**My experiment and interpretation:**

### Exercise 17: Physics loss versus trajectory error

Explain why the following are related but not identical:

1. Low residual loss at the collocation points.
2. Low residuals everywhere in the time interval.
3. Low temperature error relative to RK4.
4. Low temperature error relative to hardware measurements.

Construct one plausible example in which the training loss is small but the
RK4 trajectory error is unacceptable. State what diagnostic or experiment
would reveal the problem.

**My explanation and example:**

### Exercise 18: CPU, MPS, and reproducibility

Read `select_device` and `ForwardPINNConfig`.

1. Why is CPU the default for this small model?
2. What do `device="mps"` and `device="auto"` request?
3. What happens if MPS is explicitly requested but unavailable?
4. What role does the random seed play?
5. Why might results still differ slightly across hardware or PyTorch
   versions despite using the same seed?
6. Which quantities should be recorded to make a training result reproducible?

**My answer:**

### Checkpoint 4

Ask Codex to review Exercises 14–18 before extending the PINN.

---

## Block 5 — Scope and next extensions

### Exercise 19: Explain the constant-current restriction

The first PINN rejects a current schedule with switching times.

1. Why is the constant-current trajectory a simpler first learning problem?
2. At a rectangular current switch, which state quantities remain continuous?
3. Which temperature derivatives may jump?
4. Why can a single smooth neural network have difficulty representing a
   derivative discontinuity precisely?
5. Describe two possible future strategies: split the time domain at switches,
   or include time-dependent current while handling transition points
   explicitly.
6. Find the test that confirms switching current is currently rejected.

**My answer:**

### Exercise 20: Identify every current model limitation

For each limitation, explain the likely consequence and the experiment or data
needed to evaluate it:

1. Constant material properties.
2. No explicit thermal or electrical contact resistance.
3. Lumped cold and hot node temperatures.
4. No temperature distribution inside the module.
5. No Thomson effect.
6. Equal division of Joule heat between faces.
7. Perfectly known parameters.
8. No sensor noise, bias, lag, or location model.
9. Validation only against the conventional solver.

Then identify which limitations concern the neural network and which concern
the underlying physical model shared by both RK4 and the PINN.

**My limitation analysis:**

### Exercise 21: Design the next PINN question

Choose one next question without implementing it yet:

- Can the PINN reproduce a current pulse?
- Can one unknown physical parameter be inferred from synthetic temperatures?
- How sensitive are predictions to one uncertain parameter?
- How many temperature observations are needed to identify one parameter?

Write:

1. The single scientific question.
2. The unknown or changed quantity.
3. The data or physics information available to the model.
4. A prediction made before training.
5. A conventional-solver comparison.
6. A limiting-case, unit, or energy check.
7. A clear success criterion.

**My proposed next question:**

---

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
