# 10 — Contact-aware four-node transient model

Status: `Not started`

## Learning objectives

By the end of these exercises, I should be able to:

1. Explain why the existing two-node model remains useful.
2. Distinguish an omitted contact, a perfect contact, and a disconnected
   interface.
3. Identify the four dynamic temperatures in the contact-aware model.
4. Define the direction and sign of both contact heat rates.
5. Derive all four transient energy balances.
6. Show that internal contact heat cancels from the whole-system balance.
7. Explain how contact resistance produces face-to-exchanger temperature
   drops.
8. Trace the contact-aware right-hand side and RK4 integrator.
9. Explain the limiting-case, sign, energy, and convergence tests.
10. State which current ThermoTwin models include explicit contacts.

Make predictions before running code. Include units in every calculation.
Record mistakes in the corrections section instead of deleting them.

## Implemented baseline

The package keeps two separate conventional models:

~~~text
Shared thermoelectric equations and current schedules
|
+-- two-node model
|   +-- one lumped cold node and one lumped hot node
|   +-- no explicit face-to-exchanger contacts
|
+-- four-node contact model
    +-- cold thermoelectric face
    +-- hot thermoelectric face
    +-- cold heat exchanger
    +-- hot heat exchanger
    +-- explicit cold and hot contact resistances
~~~

The first four-node baseline makes two explicit modeling choices:

1. Each face and each heat exchanger has its own thermal capacitance.
2. External thermal loads enter the heat-exchanger nodes.

Future models may replace fixed reservoirs with flowing-fluid states or treat
some nodes as algebraic rather than dynamic.

The relevant files are:

- thermotwin/contact_transient.py: contact heat, four-node balances, and RK4;
- thermotwin/contact_diagnostics.py: aligned contact, COP, and energy histories;
- thermotwin/contact_experiments.py: the frozen generic reference case;
- thermotwin/contact_report.py: two-topology comparison and resistance sweep;
- thermotwin/transient.py: the preserved two-node model;
- thermotwin/thermoelectric.py: shared $Q_c$, $Q_h$, voltage, and power;
- thermotwin/controls.py: shared constant, step, and pulse currents; and
- tests/test_contact_*.py: signs, energy, experiments, sweep, and reporting.

---

## Block 1 — Choose the physical topology

### Exercise 1: Compare the two models

For the two-node and four-node models, list:

1. Every dynamic temperature.
2. Every thermal capacitance.
3. Where $Q_c$ is removed.
4. Where $Q_h$ is delivered.
5. Where reservoir heat enters.
6. Where external heat enters.
7. Whether a face-to-exchanger temperature drop can be represented.

| Question | Two-node model | Four-node contact model |
| --- | --- | --- |
| Number of temperatures |  |  |
| Temperatures used in $Q_c,Q_h$ |  |  |
| Explicit contact resistance |  |  |
| Explicit heat-exchanger temperature |  |  |
| Appropriate use |  |  |

**My comparison:**

### Exercise 2: Distinguish three phrases

Explain:

1. **No explicit contact model:** the interface is omitted or lumped into a
   reduced node.
2. **Perfect contact:** the interface temperature drop is zero for finite heat
   flow.
3. **Disconnected interface:** contact conductance is zero, or resistance
   tends to infinity.

Then explain why setting

~~~text
R_contact = 0
q_contact = delta_T / R_contact
~~~

does not numerically reproduce the two-node model.

**My explanation:**

### Exercise 3: Explain the modular software design

Read thermotwin/__init__.py.

1. Which functions still run the original model?
2. Which functions run the contact-aware model?
3. Which thermoelectric functions do both share?
4. Which current schedule class do both share?
5. Why are separate right-hand sides clearer than one function containing many
   contact-enabled branches?
6. What regression failure would show that the old model changed?

**My explanation:**

### Checkpoint 1

Ask Codex to review Exercises 1–3 before deriving contact heat.

---

## Block 2 — Contact heat directions and units

### Exercise 4: Cold contact heat

Cold contact heat is positive from the cold exchanger toward the cold TE face:

$$
\dot q_{\mathrm{contact},c}
=\frac{T_{x,c}-T_c}{R_{\mathrm{contact},c}}.
$$

1. State the units of the numerator and denominator.
2. Show that the result has units of watts.
3. Determine the sign when $T_{x,c}>T_c$.
4. Determine the sign when $T_{x,c}<T_c$.
5. Explain a negative result without changing the convention.

**My unit and sign analysis:**

### Exercise 5: Hot contact heat

Hot contact heat is positive from the hot TE face toward the hot exchanger:

$$
\dot q_{\mathrm{contact},h}
=\frac{T_h-T_{x,h}}{R_{\mathrm{contact},h}}.
$$

1. Why is this temperature difference ordered differently from the cold one?
2. Determine the sign when $T_h>T_{x,h}$.
3. What does a negative value mean?
4. Does the model forbid reverse heat flow?

**My explanation:**

### Exercise 6: Calculate both contact heat rates

Use:

| Quantity | Value |
| --- | ---: |
| $T_c$ | 295 K |
| $T_{x,c}$ | 300 K |
| $R_{\mathrm{contact},c}$ | 0.5 K/W |
| $T_h$ | 305 K |
| $T_{x,h}$ | 300 K |
| $R_{\mathrm{contact},h}$ | 0.25 K/W |

Calculate both contact heat rates. Repeat after doubling both resistances while
holding all temperatures fixed. Explain why fixed-temperature sensitivity is
not a complete prediction of the transient response.

**My calculations:**

### Exercise 7: Resistance versus conductance

Use

$$
G_{\mathrm{contact}}=\frac{1}{R_{\mathrm{contact}}}.
$$

1. State the units of $G_{\mathrm{contact}}$.
2. Rewrite the contact equations using conductance.
3. Which quantity becomes large for nearly perfect contact?
4. Which becomes small?
5. Why might conductance be useful in a future inverse model?

**My comparison:**

### Checkpoint 2

Ask Codex to review Exercises 4–7 before deriving the balances.

---

## Block 3 — Four transient energy balances

### Exercise 8: Cold TE-face balance

Derive:

$$
C_c\frac{dT_c}{dt}
=\dot q_{\mathrm{contact},c}-Q_c.
$$

Explain both signs, predict the direction of $T_c$ when $Q_c$ exceeds incoming
contact heat, and state which temperatures must be used inside $Q_c$.

**My derivation:**

### Exercise 9: Hot TE-face balance

Derive:

$$
C_h\frac{dT_h}{dt}
=Q_h-\dot q_{\mathrm{contact},h}.
$$

Explain both signs and predict the rate when $Q_h$ exceeds contact heat leaving
the face.

**My derivation:**

### Exercise 10: Cold exchanger balance

Derive:

$$
C_{x,c}\frac{dT_{x,c}}{dt}
=G_c(T_{c,\infty}-T_{x,c})
+\dot q_{c,\mathrm{ext}}
-\dot q_{\mathrm{contact},c}.
$$

1. Why does the reservoir term use $T_{x,c}$ rather than $T_c$?
2. Why does positive external heat enter with a plus sign?
3. Why does contact heat have the opposite sign from the cold-face balance?

**My derivation:**

### Exercise 11: Hot exchanger balance

Derive:

$$
C_{x,h}\frac{dT_{x,h}}{dt}
=G_h(T_{h,\infty}-T_{x,h})
+\dot q_{h,\mathrm{ext}}
+\dot q_{\mathrm{contact},h}.
$$

Explain every sign. If the hot reservoir is colder than the exchanger, what
sign does its heat-transfer term have?

**My derivation:**

### Exercise 12: Whole-system energy balance

Add the four balances.

1. Show that each contact heat rate cancels.
2. Substitute $Q_h-Q_c=VI$.
3. Write the total stored-energy rate.
4. Identify every term that exchanges energy with the outside.
5. Explain why contact resistance redistributes but does not create energy.

**My combined balance:**

### Checkpoint 3

Ask Codex to review Exercises 8–12 before the numerical example.

---

## Block 4 — Hand calculation and code mapping

### Exercise 13: Calculate the thermoelectric terms

Use:

| Quantity | Value |
| --- | ---: |
| $\alpha$ | 0.05 V/K |
| $R$ | 2 ohm |
| $K$ | 0.5 W/K |
| $I$ | 1 A |
| $T_c$ | 295 K |
| $T_h$ | 305 K |

Calculate the two Peltier terms, Joule heat, conductive leak, $Q_c$, $Q_h$,
voltage, and power. Verify $Q_h-Q_c=VI$.

**My calculations:**

### Exercise 14: Calculate all four rates

Use the temperatures and resistances from Exercise 6, the thermoelectric
values from Exercise 13, and:

| Quantity | Value |
| --- | ---: |
| $C_c$ | 50 J/K |
| $C_h$ | 100 J/K |
| $C_{x,c}$ | 50 J/K |
| $C_{x,h}$ | 100 J/K |
| $G_c$ | 2 W/K |
| $G_h$ | 4 W/K |
| Both reservoir temperatures | 300 K |
| $\dot q_{c,\mathrm{ext}}$ | 3 W |
| $\dot q_{h,\mathrm{ext}}$ | -4 W |

Calculate:

1. Both contact heat rates.
2. Both reservoir heat rates.
3. Net heat entering every node.
4. All four temperature rates.
5. Total stored-energy rate.
6. Reservoir heat plus external heat plus electrical power.

The final two energy rates must agree.

**My calculations:**

### Exercise 15: Map the hand calculation to code

Read four_node_contact_rhs in thermotwin/contact_transient.py.

1. Find $Q_c$ and $Q_h$.
2. Find both contact heat rates.
3. Find both reservoir heat rates.
4. Map each net heat to one balance.
5. Identify each division by capacitance.
6. Find the unit test reproducing Exercise 14.

**My code map:**

### Exercise 16: Inspect parameter validation

Read FourNodeContactThermalParameters.

1. Why must capacitances be finite and positive?
2. Why must contact resistances be finite and positive?
3. Why may reservoir conductances equal zero?
4. Why may they not be negative?
5. Why is selecting the two-node model different from passing zero contact
   resistance?

**My explanation:**

### Checkpoint 4

Ask Codex to review Exercises 13–16 before tracing RK4.

---

## Block 5 — Four-state RK4 integration

### Exercise 17: Trace one RK4 step

For a four-temperature vector $y$, expand:

~~~text
k1 = f(y_n)
k2 = f(y_n + dt*k1/2)
k3 = f(y_n + dt*k2/2)
k4 = f(y_n + dt*k3)
y_(n+1) = y_n + dt*(k1 + 2*k2 + 2*k3 + k4)/6
~~~

1. Write all four components of $y$.
2. Why is contact heat recalculated at every intermediate state?
3. Why are $Q_c$ and $Q_h$ recalculated too?
4. Which inputs remain fixed during one step?
5. What error would result from applying a slope to the wrong node?

**My trace:**

### Exercise 18: Current transitions

1. Why must an RK4 step end at a current transition?
2. Which temperatures remain continuous at a switch?
3. Which rates may jump?
4. What current applies immediately after the switch?
5. Find the contact-model pulse test and predict its time samples.

**My explanation:**

### Exercise 19: Step-size convergence

Run one contact-aware experiment at three time steps:

| Step | Final $T_c$ | Final $T_h$ | Final $T_{x,c}$ | Final $T_{x,h}$ |
| ---: | ---: | ---: | ---: | ---: |
| 0.2 s |  |  |  |  |
| 0.1 s |  |  |  |  |
| 0.05 s |  |  |  |  |

Predict which pair should agree more closely. Explain why smaller contact
resistance can require a smaller time step.

**My prediction and results:**

---

## Block 6 — Limiting cases and interpretation

### Exercise 20: Equal-temperature equilibrium

Set all four temperatures and both reservoir temperatures equal, with zero
current and zero external heat. Evaluate every heat rate and all four
derivatives.

**My derivation:**

### Exercise 21: Contact-only equilibration

Turn off thermoelectric effects, reservoir conductances, current, and external
heat. Begin each face at a different temperature from its paired exchanger.

1. Predict all four rate signs.
2. Show that each pair conserves stored energy.
3. Predict each final pair temperature by heat-capacity weighting.
4. Explain why the cold and hot pairs do not interact in this limit.

**My prediction and derivation:**

### Exercise 22: Current reversal

Start all nodes at one temperature with insulated reservoirs and no initial
contact drops. Compare equal positive and negative currents.

1. Which Peltier terms reverse?
2. Which Joule terms do not?
3. Predict the four initial rates.
4. Why is the full negative-current response not exactly the negative of the
   positive-current response when electrical resistance is nonzero?

**My prediction:**

### Exercise 23: Approach the two-node model

Split each two-node capacitance between one face and one exchanger, start each
pair at the same temperature, and progressively reduce contact resistance.

Predict what happens to:

- the face-to-exchanger temperature differences;
- aggregate stored energy on each side; and
- disagreement with the two-node trajectory.

Explain why this is a convergence experiment rather than a calculation with
$R_{\mathrm{contact}}=0$.

**My prediction:**

### Exercise 24: Distinguish $K$ from contact resistance

Compare:

~~~text
module leak = K*(Th - Tc)
contact heat = (Tface - Texchanger)/R_contact
~~~

1. Where does each heat path occur?
2. What are the parameter units?
3. Which temperatures appear?
4. Why might sparse data make the parameters correlated?
5. Why should the first inverse contact study release only one contact
   parameter while holding $K$ fixed?

**My comparison:**

### Exercise 25: Identify remaining limitations

Explain the consequence of:

1. Fixed reservoirs instead of flowing fluids.
2. Constant reservoir conductances.
3. Constant thermoelectric properties.
4. Four uniform lumped temperatures.
5. No sensor noise, bias, lag, or location model.
6. No electrical contact resistance.
7. No radiation.

Which extension is required before attempting synthetic inference of thermal
contact resistance? Which can remain deferred?

**My analysis:**

### Exercise 26: Check the frozen reference prediction

The contact reference uses 1 A, 60 s, equal 300 K starting temperatures,
equal 0.25 K/W contacts, and no external loads.

Before running it, predict:

1. Both contact heat rates at $t=0$.
2. The initial direction of both TE-face temperatures.
3. The initial direction of both exchanger temperatures.
4. Which temperature differences develop after current is applied.
5. Whether the face or exchanger temperature span becomes larger.

Run:

~~~text
python3 -m thermotwin.contact_report
~~~

Record the four final temperatures, both contact drops, both contact heat
rates, and maximum energy residual. Compare them with the predictions.

**My predictions and results:**

### Exercise 27: Module COP versus delivered COP

At the cold face,

$$
\dot q_{\mathrm{contact},c}-Q_c
=C_c\frac{dT_c}{dt}.
$$

1. Explain why $Q_c$ and cold contact heat can differ during a transient.
2. Define module cooling COP.
3. Define exchanger-delivered cooling COP.
4. Which value is more directly connected to cooling the exchanger?
5. Under what steady condition do $Q_c$ and contact heat become equal?
6. Why should an engineering report label these two COP definitions clearly?

**My explanation:**

### Exercise 28: Interpret the resistance sweep

The report evaluates equal cold and hot contact resistances of 0.1, 0.25, 0.5,
and 1.0 K/W.

Before viewing the final panel, predict how resistance affects:

1. Cold and hot contact drops.
2. Heat removed from the cold exchanger.
3. Cold face and exchanger temperatures.
4. Hot face and exchanger temperatures.
5. The difference from the reduced two-node model.

State which conditions are held fixed. After viewing the report, explain which
predictions were supported and why the sweep does not prove universal behavior
for every current, duration, load, or asymmetric contact combination.

**My prediction and interpretation:**

---

## Interview teach-back

### 30-second explanation

Why did we keep two models, and what new behavior does the four-node model add?

**My answer:**

### Two-minute explanation

Explain the four nodes, both contact signs, all four balances, whole-system
energy conservation, why the two-node model remains useful, and the most
important limiting-case test.

**My answer:**

### Challenge questions

1. Why not set contact resistance to zero to disable contacts?
2. Why do explicit contacts require additional temperatures?
3. How do you know contact terms conserve energy?
4. Why can small contact resistance make integration harder?
5. How does internal module conductance differ from interface resistance?
6. Why might two contact resistances be difficult to infer simultaneously?
7. What would a flowing-fluid extension add?

**My answers:**

---

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

> Record each important error, its consequence, and the corrected reasoning.
