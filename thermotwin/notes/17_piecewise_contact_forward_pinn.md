# Exercise sheet: piecewise contact forward PINN

This sheet develops the physics and code reasoning behind ThermoTwin's first
switched-current PINN. Complete predictions and derivations before running the
code whenever possible. The goal is to understand why the model is piecewise,
what is continuous at a switch, how the implementation enforces that behavior,
and what the RK4 comparison does and does not validate.

Relevant files:

- `thermotwin/piecewise_contact_forward_pinn.py`
- `thermotwin/piecewise_contact_forward_pinn_report.py`
- `thermotwin/contact_forward_pinn.py`
- `thermotwin/contact_transient.py`
- `thermotwin/controls.py`
- `tests/test_piecewise_contact_forward_pinn.py`
- `tests/test_piecewise_contact_forward_pinn_report.py`

Do not treat the frozen numerical answers as experimental evidence. Both the
PINN and RK4 reference solve the same assumed four-node equations.

---

## 1. Reconstruct the physical experiment

The established input is

$$
I(t)=
\begin{cases}
0\ \mathrm{A}, & 0\le t<5\ \mathrm{s},\\
1\ \mathrm{A}, & 5\le t<20\ \mathrm{s},\\
0\ \mathrm{A}, & 20\le t\le60\ \mathrm{s}.
\end{cases}
$$

1. Draw the current as a function of time.
2. Label the turn-on and turn-off transitions.
3. State the current at exactly 5 s and exactly 20 s under the
   right-continuous convention.
4. List the four modeled temperature states and identify their physical
   locations.
5. Which two thermal contact resistances separate those four nodes?
6. Which parameters are known and fixed in this forward problem?
7. Which quantities are learned functions of time?

### Prediction

Before calculating anything, predict which of the four temperatures will
initially move fastest immediately after current turns on. Explain what terms
support your prediction.

> Answer:
>

---

## 2. What changes instantly at a current switch?

Use the thermoelectric face heat rates

$$
Q_c=\alpha I T_{cf}-\frac{1}{2}I^2R-K(T_{hf}-T_{cf}),
$$

$$
Q_h=\alpha I T_{hf}+\frac{1}{2}I^2R-K(T_{hf}-T_{cf}).
$$

Assume the four temperatures have the same values immediately to the left and
right of a switch.

1. Which terms in $Q_c$ and $Q_h$ change when current jumps from 0 A to 1 A?
2. Which terms cannot jump at that instant if temperature is continuous?
3. Write expressions for $Q_c(5^-)$ and $Q_c(5^+)$.
4. Write expressions for $Q_h(5^-)$ and $Q_h(5^+)$.
5. Repeat the reasoning for the 1 A to 0 A switch at 20 s.
6. Does Joule heating have a sign change if current changes from +1 A to
   -1 A? Does the Peltier contribution?

### Interpretation

Explain why $Q_c$, $Q_h$, and temperature rates may jump even though none of
the four temperatures jumps.

> Answer:
>

---

## 3. Why temperature is continuous

For one lumped node,

$$
C\frac{dT}{dt}=\dot Q_{net}.
$$

Integrate this balance over a shrinking interval from $t_s-\epsilon$ to
$t_s+\epsilon$ around a current switch.

1. Show that

   $$
   C\left[T(t_s+\epsilon)-T(t_s-\epsilon)\right]
   =\int_{t_s-\epsilon}^{t_s+\epsilon}\dot Q_{net}\,dt.
   $$

2. If all heat rates remain finite, what happens to the integral as
   $\epsilon\rightarrow0$?
3. What does that imply about the temperature jump?
4. What nonphysical mathematical input would be required to produce a finite
   instantaneous temperature jump?
5. Would adding finite sensor lag change the continuity of the physical node
   temperature? Would it change the measured temperature trajectory?

> Derivation and interpretation:
>

---

## 4. One-sided four-node energy balances

The contact heat rates are

$$
\dot q_{cc}=\frac{T_{cx}-T_{cf}}{R_{cc}},
\qquad
\dot q_{hc}=\frac{T_{hf}-T_{hx}}{R_{hc}}.
$$

The four temperature rates are

$$
\frac{dT_{cf}}{dt}=\frac{\dot q_{cc}-Q_c}{C_{cf}},
$$

$$
\frac{dT_{hf}}{dt}=\frac{Q_h-\dot q_{hc}}{C_{hf}},
$$

$$
\frac{dT_{cx}}{dt}=
\frac{G_c(T_{c,\infty}-T_{cx})+\dot q_{c,ext}-\dot q_{cc}}{C_{cx}},
$$

$$
\frac{dT_{hx}}{dt}=
\frac{G_h(T_{h,\infty}-T_{hx})+\dot q_{h,ext}+\dot q_{hc}}{C_{hx}}.
$$

1. At turn-on, which heat-rate expressions can jump directly because they
   contain current?
2. Which two rates can jump directly at the ideal switch?
3. Which two exchanger rates initially retain their pre-switch values, and
   why?
4. Can the exchanger rates change shortly after the switch? Explain the path
   by which the new current affects them.
5. Predict how a very small face capacitance changes the sharpness of the face
   response.
6. Predict how a very large contact resistance delays the exchanger response.

> Answer:
>

---

## 5. Why one global smooth network is not exact

The original contact PINN uses `tanh` activations. A finite composition of
linear maps and `tanh` functions is differentiable everywhere.

1. What does that imply about the temperature derivative produced by one such
   network?
2. Why is a globally smooth derivative incompatible with an exact rate jump?
3. Could a single network still approximate the trajectory? Where would its
   largest error or residual likely appear?
4. Why might simply adding many collocation points at the switch be
   conceptually wrong?
5. Name two alternatives to domain decomposition for representing a switch.
6. Explain why domain decomposition is a clear first choice for a known
   piecewise-constant schedule.

> Answer:
>

---

## 6. Derive the hard continuity transform

For segment $m$, define its left and right boundaries as $a_m$ and $b_m$ and
its normalized progress as

$$
s_m(t)=\frac{t-a_m}{b_m-a_m}.
$$

ThermoTwin constructs the segment temperature vector as

$$
\mathbf T_m(t)=\mathbf T_m(a_m)
+s_m(t)T_{scale}\mathbf N_m(2s_m(t)-1).
$$

1. Substitute $t=a_m$. Show that the raw network output cannot change the
   segment's starting temperature.
2. Substitute $t=b_m$. Write the segment endpoint.
3. Set the next segment's start to that endpoint and prove
   $\mathbf T_{m+1}(a_{m+1})=\mathbf T_m(b_m)$.
4. Does this equality depend on successful optimization?
5. Differentiate the transformed output with respect to time. Which terms
   determine the derivative at a boundary?
6. Why can the left and right derivatives differ even though the temperatures
   are identical?
7. What role does `temperature_scale` play? Does it change the physical
   equations?

> Derivation:
>

---

## 7. Trace the implementation of continuity

Open `PiecewiseContactForwardPINN`.

1. Find where `_boundaries` is created.
2. Explain why the number of subnetworks is one less than the number of
   boundaries.
3. In `_temperature_with_start`, match each code expression to the transform
   in Section 6.
4. In `_segment_start_temperatures`, explain why the endpoint of an earlier
   network remains attached to PyTorch's computation graph.
5. Why is that gradient connection important during joint training?
6. In `boundary_temperature_jumps`, identify how the same switch is evaluated
   from its left and right segments.
7. Predict the returned tensor shape for two transitions and four states.
8. Explain why a zero jump here is stronger evidence than adding a continuity
   penalty that merely becomes small.

> Code notes:
>

---

## 8. Right-continuous schedule and model routing

Read `scheduled_current_tensor` and `PiecewiseContactForwardPINN.forward`.

1. Why does the current function use `time >= transition` rather than
   `time > transition`?
2. Evaluate the function manually at 4.999 s, 5 s, 19.999 s, 20 s, and
   20.001 s.
3. In `forward`, why does every nonfinal segment use a right-open mask?
4. Which subnetwork handles a query at exactly 5 s?
5. Which subnetwork handles exactly 60 s?
6. Why must the conventional reference and PINN use the same switch
   convention for pointwise comparisons?
7. Would choosing the left-continuous value change the temperature trajectory
   away from a measure-zero switch in the exact ODE? Why can it still matter
   in discrete code and tests?

> Answer:
>

---

## 9. Design the collocation set

The interval durations are 5 s, 15 s, and 40 s. The default total is 192
collocation points.

1. Compute each interval's fraction of the 60 s duration.
2. Estimate how many points proportional allocation would give each interval.
3. Read `piecewise_collocation_times` and record the exact allocation.
4. Why does every segment receive at least two points?
5. Show that the midpoint formula places every point strictly inside its
   interval.
6. Why are 5 s and 20 s excluded?
7. What bias could occur if every interval received the same number of points?
8. What bias could occur if points were allocated only by duration when one
   short segment contained much faster dynamics?
9. Propose a future adaptive collocation strategy while preserving exclusion
   of the exact switches.

> Calculations and proposal:
>

---

## 10. Follow one training iteration

Read `train_piecewise_contact_forward_pinn` and put these events in order:

- build interval boundaries;
- select the device and seed;
- create midpoint collocation times;
- evaluate known scheduled current;
- construct all segment networks;
- predict four temperature histories;
- use automatic differentiation for temperature rates;
- calculate four energy-balance residuals;
- sum their mean-squared values;
- backpropagate and update all segment weights.

Then answer:

1. Which variables does Adam update?
2. Does Adam update the current schedule?
3. Does Adam update either contact resistance?
4. Are RK4 temperatures passed to the optimizer?
5. Why is this called physics-only training?
6. If the final loss is small but RK4 error is large, list at least three
   implementation or optimization causes to investigate.

> Ordered trace and answers:
>

---

## 11. Understand the residual API change

Open `contact_physics_residuals` in `contact_forward_pinn.py`.

1. What happens when `current_values` is omitted?
2. What happens when one scheduled current is supplied for every time?
3. Why must the current tensor shape match the time tensor shape?
4. Why is retaining the omitted-current behavior important for the existing
   constant-current PINN and inverse PINN?
5. Is the scheduled current trainable or differentiable with respect to its
   switch times in this implementation?
6. What new design would be needed if the switch times themselves were
   unknown parameters?

> Answer:
>

---

## 12. Limiting cases

For each case, predict the physical result, the number of PINN segments, and a
test that should pass.

### A. Constant current

No transition lies inside the experiment.

> Prediction:
>

### B. Zero-current equilibrium

All four initial temperatures equal both reservoir temperatures; external heat
inputs are zero.

> Prediction:
>

### C. Zero-amplitude transition

The schedule contains a transition time but the current value does not change.

> Prediction and whether the implementation should simplify it:
>

### D. Switch at the experiment boundary

A schedule transition occurs at 0 s or exactly at the final duration.

> Prediction about positive-duration segmentation:
>

### E. Very small contact resistance

Both contact resistances approach zero while combined face-plus-exchanger
capacitances are held meaningful.

> Physical prediction and numerical caution:
>

### F. Reversed current

Replace the middle +1 A pulse with -1 A.

> Prediction for Peltier terms, Joule terms, and initial rate directions:
>

---

## 13. Read the tests as scientific claims

Open `tests/test_piecewise_contact_forward_pinn.py`.

For each test, write the physical or numerical claim it protects:

1. pulse boundary and interval values;
2. right-continuous current;
3. collocation exclusion of switches;
4. exact continuity with independently adjustable rates;
5. correct right-side startup residuals;
6. zero-current equilibrium;
7. short-training loss and RMSE checks; and
8. invalid-input rejection.

Then answer:

1. Which test is most directly about conservation-law physics?
2. Which test is most directly about the mathematical representation?
3. Which test would fail if `>=` were changed to `>` in the schedule?
4. Why is a limiting-case test useful even when the full training test passes?
5. Add one test idea for a bipolar pulse without implementing it yet.

> Test interpretation:
>

---

## 14. Interpret the frozen report

Run:

~~~bash
python3 -m thermotwin.piecewise_contact_forward_pinn_report
~~~

Record:

| Quantity | Your run |
| --- | ---: |
| Initial physics loss | |
| Final physics loss | |
| Maximum boundary jump | |
| Cold-face RMSE | |
| Hot-face RMSE | |
| Cold-exchanger RMSE | |
| Hot-exchanger RMSE | |

Study all six panels.

1. Where are the largest pointwise errors relative to the two switches?
2. Do the face nodes or exchanger nodes react more sharply at turn-on?
3. Why are report residuals at a switch interpreted as right-side values?
4. Does a residual spike close to a switch necessarily mean temperature is
   discontinuous?
5. Does zero constructed boundary jump prove that the trajectory is accurate?
6. Does low RK4 RMSE validate the physical model against hardware?
7. Why should the loss curve and trajectory errors both be inspected?
8. Compare your metrics with the documented frozen result and record software
   or hardware differences that might explain small variation.

> Interpretation:
>

---

## 15. Compare the three forward neural models

Complete the table without copying it directly from the README.

| Feature | Two-node PINN | Smooth contact PINN | Piecewise contact PINN |
| --- | --- | --- | --- |
| Temperature outputs | | | |
| Explicit contacts | | | |
| Current support | | | |
| Number of networks in the frozen case | | | |
| Exact initial state | | | |
| Exact switch continuity | | | |
| Can rates jump exactly? | | | |
| Uses RK4 temperatures in training? | | | |

Explain why the piecewise model was added as a separate module instead of
silently changing the original contact PINN.

> Answer:
>

---

## 16. Prepare for piecewise inverse contact inference

The next learned stage can make $R_{cc}$ trainable while retaining the
piecewise temperature architecture.

1. Which term in the four residuals contains $R_{cc}$?
2. Why should a trainable resistance be constrained to remain positive?
3. Which observed temperatures are most directly informative about $R_{cc}$?
4. Why is the turn-on or turn-off neighborhood potentially informative?
5. Why can missing readings around turn-off weaken the inference?
6. How could sensor lag be confused with contact resistance or thermal
   capacitance?
7. Why must the new inverse method first recover the ideal zero-imperfection
   limit?
8. Which should be compared on identical observations: the conventional
   scalar estimator, the inverse PINN, or both?
9. What should remain withheld until final validation?
10. State one parameter-identifiability failure that a low training loss would
    not reveal by itself.

> Answer:
>

---

## 17. Small code investigations

Perform these only after writing predictions.

1. Evaluate `scheduled_current_tensor` on times immediately around both
   switches.
2. Print `current_segment_boundaries` and `current_segment_values` for the
   frozen experiment.
3. Count collocation points in each interval.
4. Create an untrained model and evaluate `boundary_temperature_jumps`.
5. Change the raw network weights and verify that the jumps remain zero.
6. Compare left- and right-segment autograd rates at 5 s.
7. Train a deliberately tiny model and compare its loss and RK4 error with the
   default model.
8. Increase collocation density only in the shortest interval and state
   whether accuracy changes enough to justify the extra work.

For every investigation, record the hypothesis, result, and interpretation.

> Investigation log:
>

---

## 18. Final explanation in your own words

Without looking at the documentation, explain:

1. why switched current creates derivative discontinuities;
2. why temperatures remain continuous;
3. how one network per interval represents both facts;
4. how continuity is enforced exactly;
5. how current is defined at a switch;
6. why collocation excludes the switch itself;
7. what physics-only training uses;
8. what RK4 validation checks; and
9. what remains to be learned in the next inverse stage.

> Final explanation:
>

## Corrections and questions

Record mistakes, their consequences, and revised explanations here.

> Notes:
>
