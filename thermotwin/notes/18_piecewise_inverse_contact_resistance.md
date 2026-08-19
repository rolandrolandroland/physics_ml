# Exercise sheet: piecewise inverse contact resistance

This sheet develops the physics and code reasoning behind ThermoTwin's first
inverse PINN trained directly on a switched-current pulse. Complete predictions
and derivations before running code whenever possible. The goal is to
understand what parameter is inferred, what data and physics constrain it, why
one value is shared across time segments, and what the comparison can and
cannot establish.

Relevant files:

- `thermotwin/piecewise_inverse_contact_resistance.py`
- `thermotwin/piecewise_inverse_contact_resistance_report.py`
- `thermotwin/piecewise_contact_forward_pinn.py`
- `thermotwin/inverse_contact_resistance.py`
- `thermotwin/contact_forward_pinn.py`
- `thermotwin/contact_resistance_inference.py`
- `tests/test_piecewise_inverse_contact_resistance.py`
- `tests/test_piecewise_inverse_contact_resistance_report.py`

The synthetic hidden truth is available to tests and post-training validation,
but it is not supplied to the neural optimizer as a parameter label.

---

## 1. Distinguish the four contact PINN stages

Complete the table in your own words.

| Feature | Smooth forward | Smooth inverse | Piecewise forward | Piecewise inverse |
| --- | --- | --- | --- | --- |
| Current input | | | | |
| Temperature subnetworks | | | | |
| Trainable physical parameters | | | | |
| Temperature observations in loss | | | | |
| Exact switch continuity | | | | |
| Can derivatives jump exactly? | | | | |

Then answer:

1. Which previously validated component supplies switched-current temperature
   functions?
2. Which previously validated component supplies positive resistance
   parameterization and observation loss?
3. What is the only new scientific unknown in this stage?
4. Why is combining two validated capabilities safer than introducing
   switched current, multiple parameters, and imperfect sensors at once?

> Answer:
>

---

## 2. Reconstruct the inverse experiment

The training current is

$$
I(t)=
\begin{cases}
0\ \mathrm{A}, & 0\le t<5\ \mathrm{s},\\
1\ \mathrm{A}, & 5\le t<20\ \mathrm{s},\\
0\ \mathrm{A}, & 20\le t\le60\ \mathrm{s}.
\end{cases}
$$

1. Draw the schedule and mark the two switches.
2. State the right-continuous current at exactly 5 s and 20 s.
3. Which four temperatures exist in the hidden synthetic trajectory?
4. Which two temperatures are observed by the inverse PINN?
5. How often are observations sampled?
6. How many paired observation times are present?
7. How many individual temperature values enter the observation loss?
8. How many dense RK4 times are reserved for validation?
9. Which current regime is held out for validation?
10. Which current regime is held out for testing?

### Prediction

Predict whether the 0--5 s equilibrium interval, the powered interval, or the
turn-off transient is most informative about cold contact resistance. Explain
before inspecting any sensitivity results.

> Prediction:
>

---

## 3. Locate the unknown in the physics

The cold contact heat rate is

$$
\dot q_{cc}=\frac{T_{cx}-T_{cf}}{R_{cc}}.
$$

It enters the adjacent balances as

$$
\frac{dT_{cf}}{dt}=\frac{\dot q_{cc}-Q_c}{C_{cf}},
$$

$$
\frac{dT_{cx}}{dt}=
\frac{G_c(T_{c,\infty}-T_{cx})+\dot q_{c,ext}-\dot q_{cc}}{C_{cx}}.
$$

1. Differentiate $\dot q_{cc}$ with respect to $R_{cc}$ while holding both
   temperatures fixed.
2. If $T_{cx}>T_{cf}$, does increasing resistance increase or decrease the
   contact heat rate?
3. Under that same temperature ordering, how does increasing resistance
   change the required cold-face rate?
4. How does it change the required cold-exchanger rate?
5. Why do the hot residuals have no direct $R_{cc}$ term?
6. Can the hot temperatures still contain indirect information about
   $R_{cc}$? Trace the coupling path.
7. What happens to parameter sensitivity when $T_{cx}=T_{cf}$?

> Derivation and interpretation:
>

---

## 4. Explain why resistance is shared across segments

The temperature model has one subnetwork for each constant-current interval,
but the inverse model contains only one raw cold-contact-resistance parameter.

1. Count the temperature subnetworks in the frozen experiment.
2. Count the trainable resistance parameters.
3. Why can temperature derivatives differ across segment boundaries?
4. Why should the physical contact resistance remain the same at a current
   switch under the present assumptions?
5. What unphysical flexibility would three independent resistance parameters
   introduce?
6. How could segment-specific resistances conceal temperature-network error?
7. Name a real physical mechanism that might eventually justify a
   time-dependent contact resistance, and identify what additional evidence
   would be needed before adding it.

> Answer:
>

---

## 5. Positive parameterization

The model stores an unconstrained raw value and calculates

$$
R_{cc}=\mathrm{softplus}(r_{raw}).
$$

1. What range can $r_{raw}$ take?
2. What range can $R_{cc}$ take?
3. Why would zero or negative thermal contact resistance be inadmissible in
   this model?
4. Why not clamp a directly trained resistance after every update?
5. What does `inverse_softplus` calculate when the user requests an initial
   physical resistance of 0.50 K/W?
6. Does positivity guarantee identifiability?
7. Does positivity guarantee that the optimizer finds the hidden truth?

> Answer:
>

---

## 6. Prove exact temperature continuity again

For segment $m$,

$$
\mathbf T_m(t)=\mathbf T_m(a_m)
+s_m(t)T_{scale}\mathbf N_m(t),
\qquad
s_m(t)=\frac{t-a_m}{b_m-a_m}.
$$

1. Evaluate the expression at $a_m$.
2. Set $\mathbf T_{m+1}(a_{m+1})$ equal to the previous endpoint.
3. Prove that the four temperature jumps are zero at 5 s and 20 s.
4. Does a changing inferred resistance alter this proof?
5. Does the observation loss enforce continuity?
6. Why is constructed continuity stronger than a finite penalty term?
7. Explain why the derivatives can still jump.

> Proof:
>

---

## 7. Separate collocation points from observations

The default has 192 physics collocation points and 61 observation times.

1. What is evaluated at a physics collocation point?
2. What is evaluated at an observation time?
3. Which set excludes 5 s and 20 s?
4. Why does that set exclude the switches?
5. Which set includes both switches?
6. Why is a temperature observation unambiguous at a switch even though its
   derivative is not?
7. Does one observation at a switch supply both the left and right derivative?
8. Why should these two time sets not be described as interchangeable
   training labels?

> Answer:
>

---

## 8. Derive the normalized physics loss

For the four rate residuals,

$$
\mathcal L_{physics}
=\sum_{j\in\{cf,hf,cx,hx\}}
\mathrm{mean}\left[
\left(\frac{r_j}{0.1\ \mathrm{K/s}}\right)^2
\right].
$$

1. State the units of every $r_j$.
2. State the units after dividing by 0.1 K/s.
3. State the units after squaring and averaging.
4. Why is the sum dimensionless?
5. Does the scale 0.1 K/s represent a new conductance or capacitance?
6. If the scale were doubled, how would the numerical physics loss change for
   identical residuals?
7. Would the underlying differential equations change?

> Derivation:
>

---

## 9. Derive the observation loss and weighting

The cold-pair observation loss is

$$
\mathcal L_{obs}
=\mathrm{mean}\left[
\left(
\frac{T_{s,k}^{PINN}-T_{s,k}^{obs}}{1\ \mathrm{K}}
\right)^2
\right],
\qquad s\in\{cf,cx\}.
$$

The total loss is

$$
\mathcal L=\mathcal L_{physics}+20\mathcal L_{obs}.
$$

1. Show that $\mathcal L_{obs}$ is dimensionless.
2. Does its mean combine sensors and times before or after squaring?
3. Why can a flexible temperature network partially fit observations even
   when the resistance is biased?
4. What behavior did the weight 20 reduce during tuning?
5. Does multiplying the observation term by 20 add observations?
6. Does it mean the sensors are known to be twenty times more accurate?
7. What risk appears if the observation weight is far too small?
8. What risk appears if it is extremely large?
9. Why must parameter error and physics loss be reported separately?
10. Propose a systematic future way to study loss-weight sensitivity.

> Answer:
>

---

## 10. Trace one optimization epoch

Read `train_piecewise_inverse_contact_resistance` and order these operations:

- evaluate known right-continuous current at collocation times;
- predict all four temperatures;
- calculate temperature derivatives with automatic differentiation;
- calculate contact and thermoelectric heat rates;
- build four normalized physics residual terms;
- predict the cold pair at observation times;
- build normalized observation mismatch;
- combine weighted losses;
- differentiate with respect to all subnetworks and the raw resistance;
- update two Adam parameter groups.

Then answer:

1. What learning rate is used for temperature-network parameters?
2. What learning rate is used for the raw resistance?
3. Why are separate parameter groups useful?
4. Which quantities remain fixed during optimization?
5. Is the conventional estimator called during neural training?
6. Is hidden parameter truth included in the loss?
7. Are dense RK4 temperatures included in the loss?

> Ordered trace and answers:
>

---

## 11. Work through the non-identifiability limit

Assume:

- $I=0$ for the entire experiment;
- all four temperatures start at 300 K;
- both reservoirs are 300 K;
- external heat inputs are zero; and
- the temperature networks represent constant 300 K histories.

1. Calculate $Q_c$ and $Q_h$.
2. Calculate both contact heat rates.
3. Calculate all four required temperature rates.
4. Calculate all four residuals.
5. Does any result depend on $R_{cc}$?
6. What is the gradient of the physics loss with respect to the raw
   resistance?
7. Would perfect 300 K observations resolve the ambiguity?
8. Explain why this is structural non-identifiability rather than an optimizer
   failure.
9. What feature of the pulse creates a nonzero contact temperature drop and
   restores sensitivity?

> Calculation and interpretation:
>

---

## 12. Compare neural and conventional inference

Both estimators receive the same ideal long-form pulse observations.

The conventional method:

1. chooses a candidate resistance;
2. solves the four-node equations with RK4;
3. samples predicted cold temperatures at available times;
4. calculates temperature mismatch; and
5. repeats with golden-section scalar search.

The inverse PINN jointly learns three four-temperature subnetworks and one
resistance.

1. Which method optimizes only one scalar?
2. Which method approximates four continuous temperature histories as part of
   inference?
3. Which method satisfies the conventional equations only up to neural
   residual error?
4. Why should the conventional method recover exact same-model data more
   closely in this one-parameter problem?
5. What future advantage could the PINN representation provide for more
   complicated inference or data assimilation?
6. Why must both methods use identical available observations for a fair
   comparison?
7. Would closer agreement between the methods validate the equations against
   hardware?

> Comparison:
>

---

## 13. Understand withheld validation

Classify each item as `training input`, `training constraint`, `validation
only`, or `hidden truth`:

1. 61 cold-face temperatures;
2. 61 cold-exchanger temperatures;
3. hot-face RK4 history;
4. hot-exchanger RK4 history;
5. dense cold-face RK4 history;
6. known current schedule;
7. four energy-balance equations;
8. true 0.25 K/W resistance;
9. lower-amplitude validation pulse observations; and
10. bipolar test pulse observations.

Then answer:

1. Why is hot-side accuracy informative even though hot temperatures are not
   labels?
2. Why is dense same-regime validation different from parameter transfer?
3. Why is the inferred resistance inserted into the conventional solver for
   held-out schedules?
4. Why is the learned three-segment trajectory not directly evaluated on the
   bipolar schedule?

> Classification and explanation:
>

---

## 14. Interpret the frozen numerical result

Run:

~~~bash
python3 -m thermotwin.piecewise_inverse_contact_resistance_report
~~~

Record your output:

| Quantity | Your run |
| --- | ---: |
| True resistance | |
| Initial resistance | |
| PINN resistance | |
| Conventional resistance | |
| Relative parameter error | |
| Final physics loss | |
| Final observation loss | |
| Maximum boundary jump | |
| Validation transfer RMSE | |
| Test transfer RMSE | |

Then answer:

1. Did the total loss decrease monotonically?
2. Did the resistance converge monotonically?
3. Why would reporting only the final total loss conceal useful information?
4. Why is a 0.208 percent parameter error not the same quantity as a
   temperature RMSE?
5. Why can the conventional parameter estimate be closer to truth?
6. Is the neural trajectory accurate enough to validate the architecture?
7. Does it prove the real hardware contact resistance is 0.25 K/W?
8. What does exactly zero boundary jump establish?
9. What does it not establish?

> Interpretation:
>

---

## 15. Read all eight report panels

For each panel, state the question it answers:

1. face temperatures and cold-face observations;
2. exchanger temperatures and cold-exchanger observations;
3. right-continuous current;
4. four dense PINN-minus-RK4 errors;
5. four right-side physics residuals;
6. total, physics, and observation losses;
7. resistance history, truth, and conventional fit; and
8. cold contact temperature drop.

Additional questions:

1. Where do residual changes appear relative to 5 s and 20 s?
2. Why are residual values at a switch interpreted from the right?
3. Where is the cold contact temperature drop largest?
4. Does a visible loss spike imply a temperature discontinuity?
5. Why should the contact-drop panel be inspected when inferring contact
   resistance?
6. Which panel would reveal a correct parameter paired with a poor neural
   trajectory?
7. Which panel would reveal a good temperature fit paired with a biased
   parameter?

> Panel notes:
>

---

## 16. Read the tests as scientific safeguards

Open `tests/test_piecewise_inverse_contact_resistance.py`.

For each tested behavior, write the failure it would catch:

1. exact reuse of the training pulse;
2. right-continuous observation currents;
3. positive resistance and exact state interfaces;
4. one resistance shared across all segments;
5. zero-gradient equilibrium limit;
6. recovery from a wrong initial resistance;
7. conventional agreement;
8. held-out parameter transfer; and
9. invalid-input rejection.

Then open the report tests.

1. Why are history alignment checks scientifically relevant?
2. Why is the default figure directory tested?
3. Why is malformed loss history rejected rather than truncated with `zip`?
4. Why is PNG creation a weaker check than numerical report-data checks?
5. Propose one new test for reversed current.
6. Propose one new test for two different initial resistance guesses.

> Test interpretation:
>

---

## 17. Predict the measurement-imperfection sequence

The ideal baseline will be held fixed while measurement assumptions change.

For each imperfection, predict the likely effect on resistance inference and
explain the mechanism.

### A. Remove cold readings around 20 s

> Prediction:
>

### B. Keep only the cold face

> Prediction:
>

### C. Keep only the cold exchanger

> Prediction:
>

### D. Add independent 0.05 K Gaussian noise

> Prediction:
>

### E. Add +0.10 K cold-face bias

> Prediction:
>

### F. Add 2 s cold-face sensor lag but do not model it in the inverse PINN

> Prediction:
>

### G. Combine lag, bias, noise, turn-off missingness, and restricted sensors

> Prediction:
>

Which case primarily increases random spread? Which cases can produce
systematic parameter bias? Which could be confused with capacitance or contact
dynamics?

> Summary:
>

---

## 18. Small code investigations

Perform these only after writing a prediction.

1. Print the names of all trainable parameters and verify that only one name
   contains `resistance`.
2. Evaluate boundary jumps before and after a short training run.
3. Repeat a short run with observation weight 1 and compare the inferred
   resistance, physics loss, and observation loss with weight 20.
4. Repeat from initial resistances 0.10, 0.50, and 0.90 K/W.
5. Remove every second observation while retaining the same collocation set.
6. Remove the 20 s observation only.
7. Compare contact-drop sensitivity at 0.10, 0.25, and 0.50 K/W.
8. Plot the left- and right-side rates at 5 s and 20 s.
9. Compare the PINN parameter with the conventional fit on exactly the same
   reduced observation set.

For every investigation, record:

- hypothesis;
- code change or configuration change;
- numerical result;
- physical interpretation; and
- whether the result supports or contradicts the hypothesis.

> Investigation log:
>

---

## 19. Final explanation in your own words

Without looking at the documentation, explain:

1. what $R_{cc}$ physically represents;
2. where it enters the four-node equations;
3. why one value is shared across three subnetworks;
4. how positivity and temperature continuity are enforced;
5. what physics collocation points contribute;
6. what cold-pair observations contribute;
7. why the observation term has weight 20;
8. why zero contact drop destroys identifiability;
9. how the conventional comparison is made fair;
10. what dense and held-out validations establish; and
11. what remains before this becomes a hardware-calibrated digital twin.

> Final explanation:
>

## Corrections and questions

Record mistakes, their consequences, and revised explanations here.

> Notes:
>
