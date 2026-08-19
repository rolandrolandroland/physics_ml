# Inverse contact-resistance PINN: physics and code exercises

Status: Not started

This worksheet covers the first learned inference of the cold thermal contact
resistance. Complete the predictions and derivations before running the code.
The goal is to understand both why the parameter is physically learnable in
this experiment and how gradients reach it through the four-node PINN.

Main files:

- `thermotwin/contact_forward_pinn.py`: reusable four-state network and
  residual equations;
- `thermotwin/inverse_contact_resistance.py`: sparse data, positive parameter,
  joint loss, training, validation, and pulse-transfer checks;
- `thermotwin/inverse_contact_resistance_report.py`: six-panel learned versus
  conventional comparison;
- `thermotwin/contact_resistance_inference.py`: conventional scalar-search
  comparator and the unseen pulse datasets;
- `tests/test_inverse_contact_resistance.py`: physics, identifiability,
  recovery, and transfer checks; and
- `tests/test_inverse_contact_resistance_report.py`: report alignment and PNG
  checks.

---

## 1. Distinguish forward prediction from inverse inference

### Exercise 1.1 — Identify what is known and unknown

Sort these quantities into `learned`, `known and fixed`, `observed sparsely`,
and `withheld for validation`:

- $T_{cf}(t)$;
- $T_{hf}(t)$;
- $T_{cx}(t)$;
- $T_{hx}(t)$;
- cold contact resistance $R_{cc}$;
- hot contact resistance $R_{hc}$;
- module $alpha$, electrical $R$, and thermal $K$;
- four thermal capacitances;
- reservoir conductances and temperatures;
- cold-face temperatures every 5 s;
- cold-exchanger temperatures every 5 s;
- dense RK4 temperatures; and
- hot-face and hot-exchanger synthetic temperatures.

Your classification:

>

### Exercise 1.2 — Forward versus inverse contact PINN

Complete the comparison.

| Question | Contact forward PINN | Inverse contact PINN |
| --- | --- | --- |
| Temperature functions learned |  |  |
| Cold contact resistance |  |  |
| Temperature labels in loss |  |  |
| Number of physics residuals |  |  |
| Exact initial temperatures |  |  |
| Constant or switched training current |  |  |

Why is adding a trainable scalar not enough by itself to make an inverse
problem informative?

Your answer:

>

### Exercise 1.3 — State the inverse question precisely

Finish this sentence:

> Given ..., find the positive value of $R_{cc}$ and four continuous
> temperature functions such that ...

Your completed statement:

>

---

## 2. Locate the parameter in the physics

The cold contact law is

$$
\dot q_{cc}=\frac{T_{cx}-T_{cf}}{R_{cc}}.
$$

### Exercise 2.1 — Units and physical meaning

Show that $R_{cc}$ has units K/W. Explain in words what 0.25 K/W means for a
contact carrying 4 W.

Your work:

>

### Exercise 2.2 — Direct residual influence

Write the cold-face and cold-exchanger residuals in full. Circle the contact
heat in both equations.

Why does the same contact heat appear with opposite energy-flow signs?

Your equations and explanation:

>

### Exercise 2.3 — Indirect influence on all four states

$R_{cc}$ appears directly in only two residuals. Explain how changing it can
still alter the hot-face and hot-exchanger temperatures over time.

Your answer:

>

### Exercise 2.4 — Sensitivity sign at a fixed state

Hold $T_{cx}>T_{cf}$ fixed. Compare a low and high positive resistance.

Predict how increasing $R_{cc}$ changes:

1. cold contact heat;
2. the physical cold-face temperature rate;
3. the physical cold-exchanger temperature rate;
4. the cold-face residual for a fixed zero-slope trial function; and
5. the cold-exchanger residual for that same trial function.

Be careful: residual means `network rate minus physical rate`.

Your prediction:

>

### Exercise 2.5 — Differentiate contact heat with respect to resistance

At fixed temperatures, derive

$$
\frac{\partial \dot q_{cc}}{\partial R_{cc}}.
$$

When is this derivative zero? When does its magnitude become larger?

Your derivation:

>

---

## 3. Understand the synthetic observations

The inverse baseline uses constant 1 A current for 60 s. Ideal cold-face and
cold-exchanger readings are retained at

~~~text
0, 5, 10, ..., 55, 60 s.
~~~

### Exercise 3.1 — Count the data

How many observation times are present? How many scalar temperature values
enter the observation loss?

Your answer:

>

### Exercise 3.2 — Training data versus hidden truth

Why are the following not interchangeable?

- 13 sparse cold-pair observations;
- 601 dense four-state RK4 samples; and
- 128 collocation coordinates.

For each, state whether it enters training and in what role.

Your answer:

>

### Exercise 3.3 — Why use the cold sensor pair?

Explain why observing both sides of the cold contact is physically useful for
estimating its resistance. Could absolute-temperature dynamics contain
information beyond the instantaneous difference? Explain.

Your answer:

>

### Exercise 3.4 — Why keep the hot pair withheld?

The hot temperatures remain coupled through physics but are not included in
the observation loss. What can their post-training agreement reveal?

Your answer:

>

### Exercise 3.5 — Predict effects of sparser observations

Before running anything, predict how changing the interval from 5 s to 15 s
might affect:

- parameter accuracy;
- observation loss;
- dense trajectory error; and
- confidence that the result is uniquely determined.

Which direction is guaranteed, and which effects are only plausible?

Your prediction:

>

---

## 4. Understand the positive parameterization

The optimizer does not update $R_{cc}$ directly. It updates an unconstrained
raw scalar $r_{raw}$ and the physical value is

$$
R_{cc}=\mathrm{softplus}(r_{raw})
=\log(1+e^{r_{raw}}).
$$

### Exercise 4.1 — Why use a transform?

What unphysical behavior could occur if ordinary gradient descent updated the
resistance directly with no constraint?

Your answer:

>

### Exercise 4.2 — Positivity proof

Explain why softplus is positive for every finite raw value. Does it impose an
upper bound?

Your answer:

>

### Exercise 4.3 — Exact physical initialization

The code applies the inverse softplus to the requested initial physical value.
Explain why initializing the raw parameter to 0.50 would not initialize the
physical resistance to 0.50 K/W.

Your answer:

>

### Exercise 4.4 — Constraint versus information

Complete and explain:

> A positivity constraint can rule out ..., but it cannot distinguish between
> two positive values when ...

Your answer:

>

---

## 5. Derive the joint loss

### Exercise 5.1 — Physics component

Write the four-term normalized physics loss. Why is each K/s residual divided
by 0.1 K/s before squaring?

Your equation:

>

### Exercise 5.2 — Observation component

Write the observation loss for $s\in\{cf,cx\}$ and 13 times. Why does the
implementation average across both sensor columns and all times?

Your equation:

>

### Exercise 5.3 — Check dimensions

Show that the physics and observation losses are dimensionless. What would be
the units if the scales were omitted?

Your unit check:

>

### Exercise 5.4 — Numerical scale is not uncertainty

Does dividing temperature mismatch by 1 K assert that the sensor has a 1 K
standard deviation? Explain why not in this implementation.

Your answer:

>

### Exercise 5.5 — Competing objectives

Describe these failure modes:

1. observation loss is emphasized so strongly that the network interpolates
   sparse data but violates the ODEs between them; and
2. physics loss is emphasized so strongly that many parameter/trajectory
   combinations fit the equations but the selected one misses observations.

How do the report panels help reveal each?

Your answer:

>

---

## 6. Trace gradients to the resistance

### Exercise 6.1 — Follow one dependency path

Write a dependency chain from total loss to the raw resistance. Include:

~~~text
raw parameter -> softplus -> contact heat -> residual -> physics loss
~~~

Where can the observation loss influence the resistance even though its
formula contains only temperatures?

Your chain and explanation:

>

### Exercise 6.2 — Two optimizer parameter groups

Why do the network weights use learning rate $10^{-3}$ while the raw
resistance uses $5\times10^{-3}$? Is a larger parameter learning rate a
physical statement?

Your answer:

>

### Exercise 6.3 — Joint versus alternating optimization

The implementation updates the network and resistance together each epoch.
Describe an alternative alternating procedure. Give one possible advantage and
one possible drawback.

Your answer:

>

### Exercise 6.4 — Interpret loss spikes

The frozen report shows narrow late-training loss spikes even while the overall
envelope decreases and the final solution is accurate. Suggest two numerical
causes. Why should the final parameter and trajectory errors be inspected
rather than assuming a visually smooth loss is required?

Your answer:

>

---

## 7. Work through the identifiability limit

### Exercise 7.1 — Zero contact-drop experiment

Suppose current is zero and all nodes and reservoirs remain at 300 K. Show
that

$$
T_{cx}-T_{cf}=0
$$

for all time and therefore $\dot q_{cc}=0$ for every positive resistance.

Your derivation:

>

### Exercise 7.2 — Zero resistance gradient

Use your derivative from Exercise 2.5 to explain why the physics-loss gradient
with respect to the raw resistance is zero in the equilibrium test.

Your answer:

>

### Exercise 7.3 — Why more equilibrium readings do not help

Would recording the same equal-temperature equilibrium every millisecond make
$R_{cc}$ identifiable? Explain the difference between more records and more
parameter-sensitive information.

Your answer:

>

### Exercise 7.4 — Design excitation

What must an experiment do to create information about cold contact
resistance? Discuss contact temperature difference, heat flow, transient timing,
and sensor placement.

Your answer:

>

---

## 8. Trace the code

### Exercise 8.1 — Problem construction

Trace `ideal_inverse_contact_problem` through:

1. the constant-current regime;
2. the hidden physical experiment;
3. ideal observation simulation;
4. the long-form dataset; and
5. extraction of aligned cold-pair tuples.

At which step is dense truth discarded from the returned observation dataset?

Your trace:

>

### Exercise 8.2 — Model composition

Why does `InverseContactResistancePINN` contain a
`ContactForwardPINN` instead of reimplementing its neural layers and exact
initial transform?

Your answer:

>

### Exercise 8.3 — Reusable residual override

Find the optional `cold_contact_resistance` argument in
`contact_physics_residuals`.

Explain how these calls differ:

~~~python
contact_physics_residuals(model, time, experiment)
~~~

~~~python
contact_physics_residuals(
    model,
    time,
    experiment,
    cold_contact_resistance=model.cold_contact_resistance,
)
~~~

Why does the first preserve the forward model's behavior?

Your answer:

>

### Exercise 8.4 — Observation column selection

The network output order is `(CF, HF, CX, HX)`. Explain why

~~~python
predicted_temperatures[:, (0, 2)]
~~~

selects the fitted sensor pair. What mistake would `(0, 1)` introduce, and
could a tensor-shape test detect it?

Your answer:

>

### Exercise 8.5 — Validation path

Trace the three different validation operations:

1. dense constant-current PINN versus RK4 trajectories;
2. conventional scalar search on the same sparse observations; and
3. conventional simulations using the PINN resistance on unseen pulses.

Which operation validates the network function, which compares estimators,
and which tests parameter transfer?

Your answer:

>

---

## 9. Compare the neural and conventional estimators

### Exercise 9.1 — State each optimization problem

In your own words, explain what the conventional golden-section search updates
and what the inverse PINN updates.

Your answer:

>

### Exercise 9.2 — Why conventional search is extremely accurate here

The conventional fit gives about 0.250000002 K/W, while the PINN gives about
0.250140756 K/W. Give three reasons the one-dimensional conventional fit has
an easier numerical task in this ideal same-model problem.

Your answer:

>

### Exercise 9.3 — Why use a PINN anyway?

If scalar search is more accurate for one unknown parameter, what future
capabilities could justify the learned formulation? Distinguish possible
benefits from benefits actually demonstrated by the current code.

Your answer:

>

### Exercise 9.4 — Fair comparison

List the conditions that must match for a fair estimator comparison:

- physical equations;
- hidden parameter;
- current and boundary inputs;
- observation times and sensor values;
- fitted sensor set; and
- evaluation metric.

Which aspects still differ inherently between the two algorithms?

Your answer:

>

---

## 10. Understand parameter transfer to pulse regimes

### Exercise 10.1 — What is transferred?

Complete this sentence accurately:

> The validation and test pulse results transfer the learned ..., but they do
> not transfer or evaluate the learned ...

Your answer:

>

### Exercise 10.2 — Why the conventional solver is used

Why can the conventional RK4 solver use the inferred resistance under a pulse
even though the inverse PINN rejects switching-current training?

Your answer:

>

### Exercise 10.3 — Whole-regime separation

The transfer datasets use a lower-amplitude validation pulse and a bipolar
test pulse. Why is withholding complete operating regimes more informative
than randomly withholding individual times from the same 1 A trajectory?

Your answer:

>

### Exercise 10.4 — Interpret low transfer RMSE

The all-sensor transfer RMSE values are approximately:

| Regime | RMSE |
| --- | ---: |
| Lower-amplitude validation pulse | 0.000087 K |
| Bipolar test pulse | 0.000145 K |

What do these small values demonstrate? What do they not demonstrate about the
PINN, the hardware, and measurement imperfections?

Your answer:

>

---

## 11. Interpret the frozen result

| Metric | Value |
| --- | ---: |
| Hidden resistance | 0.250000000 K/W |
| Initial PINN guess | 0.500000000 K/W |
| Final PINN resistance | 0.250140756 K/W |
| Conventional estimate | 0.250000002 K/W |
| Relative PINN parameter error | 0.056303 percent |
| Final normalized physics loss | $1.113218\times10^{-4}$ |
| Final normalized observation loss | $1.388674\times10^{-6}$ |

### Exercise 11.1 — Parameter movement

Calculate the signed change from the initial to final PINN resistance. What
fraction of the initial guess is the final value?

Your work:

>

### Exercise 11.2 — Observation versus dense errors

The observed cold-face and cold-exchanger RMSE values are about 0.001460 K and
0.000805 K. The dense four-state RMSE values lie between 0.000832 K and
0.001542 K.

Why is checking dense and unobserved quantities important even when the sparse
observation loss is small?

Your answer:

>

### Exercise 11.3 — Strongest justified conclusion

Write the strongest conclusion supported by this result, including the words
`ideal`, `same-model`, `constant-current`, and `single parameter`.

Your statement:

>

### Exercise 11.4 — Unsupported conclusions

Explain why none of these claims is justified yet:

1. the physical contact resistance of a real device is 0.25 K/W;
2. the PINN is robust to 0.05 K sensor noise;
3. the PINN can distinguish contact resistance from sensor lag;
4. the PINN can train directly on pulse current; and
5. all four-node parameters are jointly identifiable.

Your answer:

>

---

## 12. Read the tests as scientific safeguards

### Exercise 12.1 — Directional sensitivity test

Explain why the fixed-state test checks both the denominator role of
$R_{cc}$ and the opposite contact signs in the face/exchanger balances.

Your answer:

>

### Exercise 12.2 — No-drop identifiability test

Why is checking a zero gradient stronger than merely checking that the
temperature solution remains constant?

Your answer:

>

### Exercise 12.3 — Recovery tolerance

The short unit-test training does not require the exact 8,000-epoch frozen
estimate. Explain why a parameter-error tolerance and trajectory tolerances are
more robust tests than exact equality across PyTorch versions.

Your answer:

>

### Exercise 12.4 — Switching-current rejection

Why should unsupported pulse training raise a clear error rather than silently
evaluate every collocation point at the initial current?

Your answer:

>

### Exercise 12.5 — Report alignment

Identify what could go wrong if observation points, dense reference times,
loss epochs, or resistance history had mismatched lengths. Which errors are
scientific and which are presentation errors?

Your answer:

>

---

## 13. Small investigations

Make predictions first and preserve the frozen defaults.

### Exercise 13.1 — Change the initial guess

Try initial resistances of 0.10, 0.25, and 0.80 K/W with otherwise identical
settings.

| Initial value | Final value | Parameter error | Final physics loss | Final observation loss |
| ---: | ---: | ---: | ---: | ---: |
| 0.10 |  |  |  |  |
| 0.25 |  |  |  |  |
| 0.80 |  |  |  |  |

Do all runs reach the same basin? Does starting at truth guarantee the final
estimate stays exactly at truth while the network is still learning?

### Exercise 13.2 — Change observation spacing

Compare 2, 5, 10, and 15 s. Record the number of paired times, parameter
error, and dense cold-pair RMSE.

| Interval | Paired times | Parameter error | CF RMSE | CX RMSE |
| ---: | ---: | ---: | ---: | ---: |
| 2 s |  |  |  |  |
| 5 s |  |  |  |  |
| 10 s |  |  |  |  |
| 15 s |  |  |  |  |

Explain why one finite experiment cannot prove a monotonic general law about
sampling interval.

### Exercise 13.3 — Change loss weights

Try a tenfold larger physics weight and a tenfold larger observation weight.
Inspect all six report panels, not only the final parameter.

Your result:

>

### Exercise 13.4 — Remove one sensor in a disposable experiment

Fit only the cold face, then only the cold exchanger. Predict which is more
informative using the conventional sensor study before running. What code
changes would be needed to make sensor selection configurable rather than
hard-coded?

Your result:

>

### Exercise 13.5 — Add ideal noise only after defining the likelihood

Do not simply add noise and reuse every numerical scale without thought.
Describe what must be decided about:

- noise distribution and standard deviation;
- independent versus correlated errors;
- per-sensor scales;
- observation weighting;
- repeated seeds; and
- parameter uncertainty summaries.

Your design:

>

---

## 14. Plan the next learned stage

### Exercise 14.1 — Time-varying current

A rectangular current switch creates a temperature-derivative discontinuity.
Compare these possible PINN strategies:

1. one smooth network with switch points excluded from residual sampling;
2. separate subnetworks on each constant-current interval with continuity
   constraints; and
3. a weak or integral-form physics loss.

For each, state one advantage and one risk.

Your comparison:

>

### Exercise 14.2 — Same imperfect datasets

Once pulse control is supported, list the conventional datasets that should be
fed to both estimators for a fair comparison:

- ideal;
- Gaussian noise;
- fixed bias;
- sensor lag;
- turn-off missingness;
- restricted sensors; and
- combined imperfections.

Which measurement effects must be explicitly modeled rather than merely
treated as random residuals?

Your answer:

>

### Exercise 14.3 — Multiple unknowns

Predict possible confounding between cold contact resistance and:

- cold-face capacitance;
- cold-exchanger capacitance;
- reservoir conductance;
- sensor bias; and
- sensor time constant.

What additional controls or sensors could help separate them?

Your answer:

>

---

## 15. Explain the complete workflow in your own words

Write a short walkthrough that answers:

1. What physical parameter is learned?
2. Where does it enter the four-node equations?
3. Why must it be positive?
4. Which temperatures are learned and which are observed?
5. What do collocation points contribute?
6. How are physics and observation loss combined?
7. How does gradient descent reach the resistance?
8. What is the exact non-identifiable limiting case?
9. How is the conventional estimator compared fairly?
10. What is transferred to the unseen pulse regimes?
11. What does the frozen result establish?
12. What remains before imperfect pulse observations can be used?

Your walkthrough:

>

---

## 16. Corrections after review

| Exercise | Original mistake | Consequence | Corrected reasoning |
| --- | --- | --- | --- |
|  |  |  |  |

## 17. Completion checklist

- [ ] I can distinguish fixed, learned, observed, and withheld quantities.
- [ ] I can locate $R_{cc}$ in both cold residuals.
- [ ] I can predict the sensitivity signs at a fixed contact drop.
- [ ] I can explain why no contact drop means no resistance information.
- [ ] I understand the softplus parameterization and inverse initialization.
- [ ] I can derive both normalized loss components and check their units.
- [ ] I can trace gradients from loss to the raw resistance.
- [ ] I can explain the two optimizer parameter groups.
- [ ] I can distinguish sparse observations from collocation coordinates.
- [ ] I understand why hot histories are withheld consistency checks.
- [ ] I can compare the neural and conventional optimization problems.
- [ ] I can state exactly what is transferred to the pulse regimes.
- [ ] I can interpret every panel in the inverse report.
- [ ] I can state why the result is not hardware validation.
- [ ] I can explain why time-varying current is the next learned-model step.
