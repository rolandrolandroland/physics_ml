# Contact-aware forward PINN: physics and code exercises

Status: Not started

Use this worksheet to understand the fixed-parameter four-node forward PINN
before contact resistance becomes an inferred parameter. Write predictions and
derivations before running code. When you do run code, compare the result with
your prediction and explain any disagreement.

The main implementation files are:

- `thermotwin/contact_transient.py`: conventional four-node equations and RK4;
- `thermotwin/contact_experiments.py`: frozen physical experiment;
- `thermotwin/contact_forward_pinn.py`: four-output network, residuals,
  training, prediction, and validation;
- `thermotwin/contact_forward_pinn_report.py`: aligned RK4/PINN report data and
  six-panel figure;
- `tests/test_contact_forward_pinn.py`: equation, limiting-case, and training
  checks; and
- `tests/test_contact_forward_pinn_report.py`: report alignment and PNG checks.

Do not use the RK4 temperatures to answer what the PINN sees during training.
Keeping training information separate from validation information is one of
the central ideas in this worksheet.

---

## 1. State the modeling problem

### Exercise 1.1 — Identify the four thermal states

Complete the state vector in the exact code order:

$$
\mathbf T(t)=
\begin{bmatrix}
\underline{\hspace{2cm}} \\
\underline{\hspace{2cm}} \\
\underline{\hspace{2cm}} \\
\underline{\hspace{2cm}}
\end{bmatrix}.
$$

For each state, say what physical body is assumed to have one uniform
temperature.

Your answer:

>

### Exercise 1.2 — Explain why there are four states

Why can the cold exchanger and cold thermoelectric face have different
temperatures? Answer the same question for the hot side.

Your answer:

>

### Exercise 1.3 — Compare the two forward PINNs

Complete the table without looking at the detailed README.

| Question | Two-node forward PINN | Contact-aware forward PINN |
| --- | --- | --- |
| Network input |  |  |
| Network outputs |  |  |
| Explicit contact resistance? |  |  |
| Number of ODE residuals |  |  |
| Parameters inferred during training |  |  |
| Current schedule currently accepted |  |  |

Then explain why the contact-aware model is not merely a larger neural network
for the same physical problem.

Your answer:

>

---

## 2. Reconstruct the four-node physics

Use the following sign definitions:

- positive $Q_c$ leaves the cold thermoelectric face and enters the module;
- positive $Q_h$ leaves the module and enters the hot thermoelectric face;
- positive $\dot q_{cc}$ goes from cold exchanger to cold face;
- positive $\dot q_{hc}$ goes from hot face to hot exchanger; and
- positive external heat enters its exchanger node.

### Exercise 2.1 — Contact heat rates

Complete both contact laws:

$$
\dot q_{cc}=\frac{\underline{\hspace{2cm}}
-\underline{\hspace{2cm}}}{R_{cc}},
$$

$$
\dot q_{hc}=\frac{\underline{\hspace{2cm}}
-\underline{\hspace{2cm}}}{R_{hc}}.
$$

Check the units. Show that kelvin divided by kelvin per watt gives watts.

Your unit check:

>

### Exercise 2.2 — Thermoelectric heat rates use face temperatures

Write $Q_c$ and $Q_h$ for the contact model. Clearly identify which two of the
four temperatures appear in the Peltier and conductive terms.

Your equations:

>

Why would using exchanger temperatures inside $Q_c$ and $Q_h$ erase part of
the physical meaning of the contact resistances?

Your explanation:

>

### Exercise 2.3 — Complete all four energy balances

Fill in the missing terms and signs:

$$
C_{cf}\frac{dT_{cf}}{dt}
=\underline{\hspace{2cm}}-\underline{\hspace{2cm}},
$$

$$
C_{hf}\frac{dT_{hf}}{dt}
=\underline{\hspace{2cm}}-\underline{\hspace{2cm}},
$$

$$
C_{cx}\frac{dT_{cx}}{dt}
=G_c(T_{c,\infty}-T_{cx})
+\dot q_{c,\mathrm{ext}}
-\underline{\hspace{2cm}},
$$

$$
C_{hx}\frac{dT_{hx}}{dt}
=G_h(T_{h,\infty}-T_{hx})
+\dot q_{h,\mathrm{ext}}
+\underline{\hspace{2cm}}.
$$

For every term, state whether positive heat makes the corresponding node
warmer or cooler.

Your sign explanation:

>

### Exercise 2.4 — Internal contact-energy cancellation

Add the cold-face and cold-exchanger stored-energy rates. Which contact term
cancels? Repeat for the hot pair.

Then add all four balances. Which terms remain as exchanges with the entire
four-node system?

Your derivation:

>

### Exercise 2.5 — Convert balances into residuals

For each balance, divide by its capacitance and write

$$
r_j=left(\frac{dT_j}{dt}\right)_{\mathrm{network}}
-\left(\frac{dT_j}{dt}\right)_{\mathrm{physics}}.
$$

Write all four expanded residual equations. What are their units?

Your residuals:

>

---

## 3. Hand-check the frozen initial condition

The frozen reference begins with all four nodes and both reservoirs at 300 K,
with 1 A current and no external heat. Its parameters include:

| Parameter | Value |
| --- | ---: |
| $\alpha$ | 0.05 V/K |
| electrical $R$ | 2 ohm |
| module $K$ | 0.5 W/K |
| $C_{cf}$ | 50 J/K |
| $C_{hf}$ | 100 J/K |
| $C_{cx}$ | 50 J/K |
| $C_{hx}$ | 100 J/K |
| $R_{cc}$ | 0.25 K/W |
| $R_{hc}$ | 0.25 K/W |

### Exercise 3.1 — Predict before calculating

At the instant current turns on, predict the signs of:

- $Q_c$;
- $Q_h$;
- $\dot q_{cc}$ and $\dot q_{hc}$; and
- each of the four temperature derivatives.

Your prediction:

>

### Exercise 3.2 — Calculate the initial heat rates

Calculate $Q_c$, $Q_h$, $\dot q_{cc}$, and $\dot q_{hc}$ at $t=0$.

Your work:

>

### Exercise 3.3 — Calculate all four initial slopes

Calculate the four rates in K/s. The associated unit test expects:

~~~text
cold face:      -0.28 K/s
hot face:       +0.16 K/s
cold exchanger:  0.00 K/s
hot exchanger:   0.00 K/s
~~~

Explain physically why the exchanger slopes are initially zero even though
the thermoelectric module immediately pumps heat.

Your work and explanation:

>

### Exercise 3.4 — Explain what happens just after startup

Once the cold face becomes colder than the cold exchanger, what signs do you
expect for the cold contact drop and cold contact heat? Once the hot face
becomes hotter than the hot exchanger, answer the same question on the hot
side.

Your answer:

>

---

## 4. Understand the neural-network representation

### Exercise 4.1 — Trace the tensor shapes

For 128 collocation times, fill in each shape:

| Quantity | Shape |
| --- | --- |
| Input time before reshape |  |
| Input time after reshape |  |
| Normalized network input |  |
| Raw network output |  |
| Initial-temperature buffer |  |
| Final temperature output |  |
| One residual column |  |

What kind of error could occur if the code and physics disagreed about the
four output columns?

Your answer:

>

### Exercise 4.2 — Prove exact initial conditions

The output transform is

$$
T_j(t)=T_j(0)
+\frac{t}{t_{\mathrm{end}}}T_{\mathrm{scale}}N_j(t).
$$

Substitute $t=0$. Why is the result independent of every network weight?

Your proof:

>

### Exercise 4.3 — Differentiate the output transform

Use the product rule to derive $dT_j/dt$. Does the transform force the initial
slope to zero? Explain why this matters for the nonzero cold- and hot-face
startup slopes.

Your derivation:

>

### Exercise 4.4 — Separate numerical scaling from physics

What does `temperature_scale=10.0` do? Why is it not a thermal capacitance,
temperature measurement, or new fitted physical parameter?

Your answer:

>

---

## 5. Understand automatic differentiation

### Exercise 5.1 — Why time requires gradients

Locate `contact_physics_residuals`. Explain the purpose of:

~~~python
differentiable_time = time.clone().detach().requires_grad_(True)
~~~

Address `clone`, `detach`, and `requires_grad_` separately.

Your explanation:

>

### Exercise 5.2 — Four derivatives from one network

Trace how the four output columns are sliced and passed to
`torch.autograd.grad`. Why does each call return a derivative with shape
`(samples, 1)`?

Your answer:

>

### Exercise 5.3 — Why training needs a derivative graph

The code asks autograd to create and retain a graph while calculating the time
derivatives. Explain the two levels of differentiation involved:

1. derivative of temperature with respect to time; and
2. derivative of the resulting physics loss with respect to network weights.

What failure would you expect if the graph were released after the fourth
time derivative but before `loss.backward()`?

Your answer:

>

### Exercise 5.4 — Compare autograd with RK4

Does autograd advance a state from one time to the next? Does RK4 represent the
entire trajectory with one neural network? Explain the different roles of the
two methods.

Your answer:

>

---

## 6. Understand the loss and training information

### Exercise 6.1 — Reconstruct the loss

Write the complete scalar physics loss from the four residual columns. If the
four mean-squared terms are 1, 4, 9, and 16 K$^2$/s$^2$, what is the total?

Your work:

>

### Exercise 6.2 — What does the optimizer see?

Sort these items into `seen during training` and `withheld for validation`:

- 128 collocation times;
- four initial temperatures;
- physical parameters;
- current and reservoir inputs;
- RK4 temperature histories;
- four ODE residual equations; and
- RK4-versus-PINN RMSE.

Your answer:

>

### Exercise 6.3 — Why this is physics-informed

There are no labeled temperatures in the forward loss. Explain what provides
the training signal and why the initial-value problem can still select a
particular physical trajectory.

Your answer:

>

### Exercise 6.4 — Equal weighting is a choice

The four residuals share units, but their typical magnitudes can differ. Give
one reason equal weighting may work here and one situation in which residual
scaling or adaptive weighting might become helpful.

Your answer:

>

### Exercise 6.5 — Interpret a small physics loss carefully

Could the following all be true at once?

- the trained PINN has a small residual loss;
- it closely matches RK4;
- the underlying physical equations are wrong for real hardware.

Explain.

Your answer:

>

---

## 7. Read and trace the implementation

### Exercise 7.1 — Configuration path

Starting at `ContactForwardPINNConfig`, trace where each setting is consumed:

- hidden width and layer count;
- collocation point count;
- epoch count and learning rate;
- temperature scale;
- random seed; and
- device.

Record the function and relevant statement for each.

Your trace:

>

### Exercise 7.2 — Training loop in your own words

Explain one epoch of `train_contact_forward_pinn` in this order:

1. clear old parameter gradients;
2. evaluate temperatures and residuals;
3. reduce the residuals to one scalar;
4. calculate parameter gradients; and
5. update the weights.

Why are RK4 temperatures absent from these steps?

Your explanation:

>

### Exercise 7.3 — Prediction schema

Why does `predict_contact_trajectory` return the same
`FourNodeContactTemperatureTrajectory` type as the conventional solver?
Identify two downstream comparisons this common schema makes safer.

Your answer:

>

### Exercise 7.4 — Validation path

Trace `validate_contact_pinn_against_rk4` from experiment to final RMSE. Where
is RK4 first called? At what time coordinates is the PINN evaluated? Why does
aligned time matter?

Your trace:

>

### Exercise 7.5 — Constant-current guard

Find `_constant_current`. Why does this first PINN reject a piecewise schedule
with actual transition times? What difficulty does an ideal current switch
introduce for a single smooth tanh network?

Your answer:

>

---

## 8. Understand the tests as scientific checks

### Exercise 8.1 — Initial-slope test

Read
`test_initial_hand_calculated_rates_make_all_residuals_zero`. Explain why a
zero result simultaneously checks:

- state ordering;
- $Q_c$ and $Q_h$ signs;
- contact signs at equal temperatures;
- capacitance division; and
- autograd temperature derivatives.

Your explanation:

>

### Exercise 8.2 — Arbitrary-state cross-check

The test at 295, 305, 300, and 300 K first asks the conventional RHS for four
rates and then embeds those slopes in a linear differentiable model. What bug
could this catch that the equal-temperature startup test might miss?

Your answer:

>

### Exercise 8.3 — Equilibrium limiting case

Explain why zero current, equal node/reservoir temperatures, and zero external
heat must produce four zero residuals for a constant-temperature network.

Which nonzero term would reveal each of these mistakes?

- wrong contact sign;
- unintended external heat;
- wrong reservoir-temperature reference; and
- nonzero network slope.

Your answer:

>

### Exercise 8.4 — Training test versus regression test

The short test requires decreasing loss and four RMSE values below 0.5 K. Why
is a tolerance better than requiring the exact frozen 3,000-epoch RMSE values
in every unit-test run?

Your answer:

>

---

## 9. Interpret the frozen report

The documented default CPU result is:

| Quantity | Value |
| --- | ---: |
| Initial physics loss | $3.282427\times10^{-1}$ K$^2$/s$^2$ |
| Final physics loss | $1.134535\times10^{-4}$ K$^2$/s$^2$ |
| Cold-face RMSE | 0.024984 K |
| Hot-face RMSE | 0.003482 K |
| Cold-exchanger RMSE | 0.015086 K |
| Hot-exchanger RMSE | 0.004939 K |

### Exercise 9.1 — Loss reduction

Approximately how many orders of magnitude does the physics loss fall? Why
does this fact alone not provide the temperature RMSE values?

Your work:

>

### Exercise 9.2 — Identify the hardest state

Which state has the largest RMSE? Suggest two numerical reasons it may be
harder to approximate in this experiment. Do not claim a physical cause unless
the figure or equations support it.

Your answer:

>

### Exercise 9.3 — Why plot pointwise errors?

Two models can have the same RMSE but very different error histories. Describe
one localized failure RMSE could hide and identify which report panel would
expose it.

Your answer:

>

### Exercise 9.4 — Contact drops as derived validation

The network does not have separate output neurons for contact temperature
drops. Explain how the report calculates them. Why does agreement of the drops
test a physically meaningful combination of outputs?

Your answer:

>

### Exercise 9.5 — State the strongest justified conclusion

Complete this sentence precisely:

> For the frozen constant-current synthetic experiment, the four-output PINN
> can ...

Then write one conclusion that the result does **not** justify.

Your answer:

>

---

## 10. Predict parameter and topology changes

Make each prediction before changing code.

### Exercise 10.1 — Larger contact resistance

If both contact resistances increase while the current and other parameters
stay fixed, predict how the face-to-exchanger temperature drops change. Does
that statement alone prove how all four absolute temperatures change?

Your prediction:

>

### Exercise 10.2 — Larger face capacitance

If $C_{cf}$ doubles, what happens to the instantaneous cold-face rate for an
unchanged thermal state and heat flows? What does not necessarily double or
halve over the whole nonlinear trajectory?

Your prediction:

>

### Exercise 10.3 — Zero-current equilibrium

Set current to zero while keeping all nodes and reservoirs at 300 K. Predict
the PINN solution, all four residuals, and all contact drops.

Your prediction:

>

### Exercise 10.4 — Unequal initial contact temperatures

Suppose $T_{cx}>T_{cf}$ initially with no module or reservoir heat flow. Which
node warms and which cools? Show that the contact heat removed from one node is
added to the other in watts even when their temperature rates differ.

Your work:

>

### Exercise 10.5 — Reduced topology is not zero resistance

Why should a user choose the separate two-node model to omit contacts instead
of setting a four-node contact resistance to zero? Address both the equation
division by resistance and the limiting stiffness of the dynamics.

Your answer:

>

---

## 11. Prepare for inverse contact-resistance inference

The next planned learned stage will keep the four temperature functions but
make at least the cold contact resistance trainable.

### Exercise 11.1 — Where resistance enters

Circle every residual containing $R_{cc}$. Does the cold contact resistance
affect only one state equation? Explain its direct and indirect influence.

Your answer:

>

### Exercise 11.2 — What observations add

Why is residual-only forward training enough when $R_{cc}$ is known, but not
generally enough to identify an unknown $R_{cc}$? Describe the role of
temperature observations in selecting a parameter value.

Your answer:

>

### Exercise 11.3 — Which sensors are informative?

Rank these sensor sets for learning the cold contact resistance and explain
your physics:

1. cold face plus cold exchanger;
2. cold face only;
3. cold exchanger only; and
4. hot face plus hot exchanger.

Compare your answer with the conventional sensitivity study in note 14 only
after writing your prediction.

Your ranking and explanation:

>

### Exercise 11.4 — Resistance versus sensor lag

Explain how both a larger contact resistance and a lagged temperature sensor
might change the apparent timing or magnitude of a measured contact response.
What extra model, sensor, or experiment information could help distinguish
them?

Your answer:

>

### Exercise 11.5 — Design the inverse validation split

Propose which current regime should be used for fitting and which different
regime should be withheld. State what successful transfer would demonstrate
and what same-model synthetic transfer still would not demonstrate.

Your proposal:

>

---

## 12. Small code investigations

Do these only after finishing the predictions above. Keep each change local;
do not overwrite the frozen defaults.

### Exercise 12.1 — Inspect initial residuals

Create the untrained model with the frozen seed and print the four residuals at
$t=0$. Explain why random initial network slopes need not equal the physical
startup slopes even though the temperatures themselves are exactly 300 K.

Your observation:

>

### Exercise 12.2 — Compare training lengths

Run 100, 500, and 3,000 epochs with the same seed. Record final physics loss
and all four RMSE values.

| Epochs | Final loss | CF RMSE | HF RMSE | CX RMSE | HX RMSE |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 100 |  |  |  |  |  |
| 500 |  |  |  |  |  |
| 3,000 |  |  |  |  |  |

Do all errors decrease monotonically with the scalar training loss? Explain
why they need not.

### Exercise 12.3 — Collocation density

Compare 32 and 128 collocation points while keeping the other settings fixed.
Inspect both RMSE and the residual curves between the training coordinates.

Your result:

>

### Exercise 12.4 — Reproducibility

Run the same configuration twice with seed 11, then once with a different
seed. Which quantities match exactly on your system? Which may change across
PyTorch versions or hardware?

Your result:

>

### Exercise 12.5 — Deliberate state-order bug

On a temporary branch or in a disposable copy, exchange two output slices in
`contact_physics_residuals` without changing prediction output ordering. Which
tests fail? Why is a shape check alone unable to detect this mistake?

Your result:

>

---

## 13. Final explanation in your own words

Write a short walkthrough that answers all of these questions without copying
the README:

1. What physical system does the four-node model represent?
2. What are the network input and four outputs?
3. How are all four initial conditions enforced?
4. How are the four residuals constructed?
5. What data does training see?
6. What role does RK4 play?
7. What does the report validate?
8. Why is this still a forward rather than inverse problem?
9. What will have to change to infer contact resistance?
10. What claim about real hardware is not yet justified?

Your walkthrough:

>

---

## 14. Corrections after review

Record exact errors rather than replacing the original answer silently.

| Exercise | Original mistake | Physical or code consequence | Corrected reasoning |
| --- | --- | --- | --- |
|  |  |  |  |

## 15. Completion checklist

- [ ] I can state the four temperatures in the implemented order.
- [ ] I can derive all four balances and residuals with correct signs.
- [ ] I can reproduce the four initial slopes by hand.
- [ ] I understand why contact heat cancels in the whole-system balance.
- [ ] I can prove that the four initial temperatures are exact.
- [ ] I understand why autograd must preserve a derivative graph for training.
- [ ] I can distinguish collocation coordinates from temperature observations.
- [ ] I can trace one training epoch through the code.
- [ ] I can explain why RK4 is withheld until validation.
- [ ] I can interpret RMSE, pointwise errors, residuals, and contact drops.
- [ ] I can state the difference between the two-node and contact-aware PINNs.
- [ ] I can explain why fixed contact resistance makes this a forward problem.
- [ ] I can identify what the next inverse contact model must add.
- [ ] I can state why synthetic RK4 agreement is not hardware validation.
