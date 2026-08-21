# ThermoTwin: detailed physics and implementation guide

This document is the tutorial-style companion to the concise
[`README.md`](README.md). It explains what the package currently does, the
physical meaning of its equations, how the conventional and learned models are
connected, and how to run and validate each stage.

The complete development sequence, revised definitions of done, and current
milestone status are maintained in [`ROADMAP.md`](ROADMAP.md). That roadmap
supersedes the original planning draft when their requirements differ.

ThermoTwin is being developed as a physics-informed digital twin and experiment
planner for a modular thermoelectric heat pump. The current package is the
foundation of that larger goal. It contains:

1. A constant-property thermoelectric model.
2. A two-node transient thermal model.
3. A separate four-node model with explicit thermal contact resistances.
4. Constant, step, and pulse current inputs.
5. Dependency-free RK4 reference solvers.
6. Derived heat, voltage, power, COP, contact, and energy histories.
7. Reproducible 1 A two-node and contact-aware reference experiments.
8. A contact-resistance sweep and two-topology comparison report.
9. An ideal virtual test stand with explicit sensors and sampled observations.
10. Reproducible Gaussian temperature noise with per-sensor configuration.
11. Fixed per-sensor temperature bias and a combined noise-plus-bias workflow.
12. First-order per-sensor dynamic lag applied before output sampling.
13. Deterministic per-sensor missing-observation intervals.
14. Whole-regime train, validation, and test experiment datasets.
15. Self-contained experiment/ground-truth provenance and ordered measurement
    transformation histories on generated datasets.
16. An automated dataset-quality audit for completeness, ranges, provenance,
    truth availability, and whole-regime split integrity.
17. Conventional least-squares inference of one cold contact resistance.
18. A 100-trial Gaussian-noise robustness study of that inference.
19. Fixed-bias inference cases separating individual, common, and differential
    cold-sensor offsets.
20. Dense-before-sparse sensor-lag inference cases.
21. Regime-aligned turn-off missingness and a local information metric.
22. Cold-face, cold-exchanger, hot-pair, and all-sensor availability studies.
23. A 100-trial combined-imperfections inference study.
24. A two-output forward physics-informed neural network, or PINN.
25. A four-output contact-aware forward PINN with fixed physical parameters.
26. A domain-decomposed four-output contact PINN for piecewise-constant
    current, with exact temperature continuity at current switches.
27. A piecewise inverse PINN that infers one shared cold contact resistance
    from the established training pulse.
28. A one-command PINN showcase combining physics-only prediction, inverse
    calibration, withheld-state validation, and unseen-control transfer.
29. RK4-versus-PINN comparison reports for the learned topologies.
30. A first inverse PINN that infers the module thermal conductance $K$ from
   sparse synthetic temperature observations.
31. A smooth four-state inverse PINN that infers the cold contact resistance and
    transfers it to unseen pulse regimes.
32. Joint contact-resistance, sensor-lag, and sensor-bias inference using only
    cold- and hot-exchanger temperatures, including missing records.
33. Local sensitivity intervals, parameter correlations, hidden-face
    reconstruction, and whole-regime transfer for the accessible-sensor case.
34. A fair periodic continuous-versus-pulsed comparison at matched delivered
    cooling with energy-storage and temperature checks.
35. Constrained next-pulse selection using expected joint information and a
    repeated-noise validation against a naive pulse.
36. Standardized synthetic assembly thermal fingerprints and contact-loss
    classifications.
37. A validated CSV bridge and explicit protocol for future hardware data.
38. A one-command four-panel engineering decision showcase.
39. Algebraic two-node and four-node steady-state solvers for fast operating
    sweeps, independently checked against zero-rate balances and RK4.
40. Cooling/heating COP maps over current, external temperature lift, contact
    resistance, and reduced versus explicit-contact topology.
41. A connection between the optimized seconds-scale pulse study and the
    steady continuous-current COP envelope.
42. A thermally averaged power-electronics layer using mean and mean-square
    current, with direct and smoothed PWM cases and separate wall-plug power.
43. Unit, sign, energy, sampling, measurement, numerical, PINN, and
    identifiability tests.

The package does **not** yet represent a hardware-validated digital twin. Its
learned models are currently validated against the conventional equations that
generated their synthetic reference data.

---

## 1. How to use this documentation

There are five documentation layers:

- [`README.md`](README.md) is the concise package reference.
- `README_detailed.md`, this file, is the step-by-step technical walkthrough.
- [`PINN_SHOWCASE.md`](PINN_SHOWCASE.md) is the focused reproducible case study.
- [`ROADMAP.md`](ROADMAP.md) defines the complete project sequence and current
  milestone exit criteria.
- [`notes/00_index.md`](notes/00_index.md) links to learning exercises,
  user-authored explanations, predictions, corrections, and derivations.

The concise and detailed READMEs describe the current implemented behavior.
The notes preserve the learning process and may contain unfinished answers.

---

## 2. Quick start

Run commands from the repository root, the directory that contains both
`thermotwin/` and `tests/`.

### 2.1 Run the conventional model tests

The conventional thermoelectric model and RK4 solver use only the Python
standard library. Run all current ThermoTwin tests with:

```bash
python3 -m unittest discover -s tests
```

The current suite contains 331 focused tests. Optional learned-model and report
tests are skipped
when their optional dependencies are not installed.

### 2.2 Install the optional learned-model dependencies

The forward and inverse PINNs require PyTorch. The contact and PINN reports
require Matplotlib:

```bash
python3 -m pip install -r thermotwin/requirements-pinn.txt
```

### 2.3 Run the main workflows

Run the focused physics-only and inverse-PINN showcase:

```bash
python3 -m thermotwin.pinn_showcase
```

Run the CPU-first engineering decision showcase:

```bash
python3 -m thermotwin.engineering_showcase
```

This runs the sparse accessible-sensor inference, fair control comparison,
next-experiment selection, and synthetic assembly-fingerprint study. It writes
`thermotwin/figures/engineering_decision_showcase.png` and prints every
principal result. The generated figure is ignored by Git and reproducible from
the committed source.

Train and validate the forward PINN:

```bash
python3 -m thermotwin.forward_pinn
```

Generate the four-panel forward comparison report:

```bash
python3 -m thermotwin.forward_pinn_report
```

Train the four-node contact-aware forward PINN and generate its six-panel
comparison report:

```bash
python3 -m thermotwin.contact_forward_pinn_report
```

Train the switched-current four-node PINN and generate its six-panel
comparison report:

```bash
python3 -m thermotwin.piecewise_contact_forward_pinn_report
```

Infer cold contact resistance from the switched-current pulse and generate its
eight-panel report:

```bash
python3 -m thermotwin.piecewise_inverse_contact_resistance_report
```

Infer the cold contact resistance and generate the neural-versus-conventional
comparison report:

```bash
python3 -m thermotwin.inverse_contact_resistance_report
```

Generate the contact-aware comparison and resistance sweep:

~~~bash
python3 -m thermotwin.contact_report
~~~

Generate the steady cooling/heating COP operating map:

~~~bash
python3 -m thermotwin.cop_operating_map_report
~~~

Place the optimized seconds-scale pulse results on that steady map:

~~~bash
python3 -m thermotwin.pulse_operating_map_report
~~~

Generate the direct-versus-smoothed averaged PWM and wall-power report:

~~~bash
python3 -m thermotwin.pwm_power_electronics_report
~~~

Audit virtual dataset provenance, completeness, ranges, and whole-regime
splits:

~~~bash
python3 -m thermotwin.dataset_quality
~~~

Run the first inverse problem and infer $K$:

```bash
python3 -m thermotwin.inverse_thermal_conductance
```

All report commands write to `thermotwin/figures/` by default. The shared
location is defined in `figure_paths.py`, created automatically when needed,
and ignored by Git because generated PNG reports are outputs rather than source
code. Pass `--output PATH` to a report command when a deliberate alternate
location is required.

---

## 3. The physical picture

The reduced model treats the heat pump and its surroundings as two lumped
thermal nodes connected by one thermoelectric module:

```text
cold reservoir                                  hot reservoir
 T_c,∞                                              T_h,∞
   │                                                   │
   │ G_c                                               │ G_h
   ▼                                                   ▼
[cold node at T_c] ⇄ [thermoelectric module] ⇄ [hot node at T_h]
        ▲                                             ▲
        │ q̇_c,ext                                    │ q̇_h,ext
```

The cold and hot nodes store thermal energy. The thermoelectric module is
treated as quasi-steady: it transports and generates heat, but it does not
store energy internally. Reservoirs exchange heat with their corresponding
nodes through effective conductances $G_c$ and $G_h$.

The contact-aware model separates the TE faces from the exchanger nodes:

~~~text
cold reservoir -> cold exchanger -> cold TE face
                      contact Rc        |
                                        | thermoelectric module
                      contact Rh        |
hot reservoir  <- hot exchanger  <- hot TE face
~~~

This adds two temperatures and makes both interface drops observable in the
simulation. The shared $Q_c$ and $Q_h$ equations use the TE-face temperatures.

The word **external** means external to the modeled thermoelectric module and
two-node heat-transfer paths. For example, an electronic component heating the
cold node can be represented by $\dot q_{c,\mathrm{ext}}>0$.

---

## 4. Symbols, meanings, and units

| Symbol | Code name | Meaning | Units |
| --- | --- | --- | --- |
| $T_c$ | `cold_temperature` | Cold-node/module-face temperature | K |
| $T_h$ | `hot_temperature` | Hot-node/module-face temperature | K |
| $T_{c,\infty}$ | `cold_reservoir_temperature` | Cold reservoir temperature | K |
| $T_{h,\infty}$ | `hot_reservoir_temperature` | Hot reservoir temperature | K |
| $I$ | `current` | Signed module current | A |
| $\alpha$ | `seebeck_coefficient` | Effective Seebeck coefficient | V/K |
| $R$ | `electrical_resistance` | Module electrical resistance | ohm |
| $K$ | `thermal_conductance` | Internal parasitic thermal conductance | W/K |
| $C_c$ | `cold_thermal_capacitance` | Cold-node thermal capacitance | J/K |
| $C_h$ | `hot_thermal_capacitance` | Hot-node thermal capacitance | J/K |
| $G_c$ | `cold_reservoir_conductance` | Cold node-to-reservoir conductance | W/K |
| $G_h$ | `hot_reservoir_conductance` | Hot node-to-reservoir conductance | W/K |
| $Q_c$ | `cold_heat` | Heat rate removed from the cold node | W |
| $Q_h$ | `hot_heat` | Heat rate delivered to the hot node | W |
| $V$ | `voltage` | Module terminal voltage | V |
| $VI$ | `electrical_power` | Signed electrical power entering the module | W |
| $\dot q_{c,\mathrm{ext}}$ | `cold_external_heat` | External heat entering cold node | W |
| $\dot q_{h,\mathrm{ext}}$ | `hot_external_heat` | External heat entering hot node | W |

Although $Q_c$ and $Q_h$ do not contain dots in the package notation, they are
heat-transfer **rates**, measured in watts. A heat quantity would be measured
in joules; a heat-transfer rate is measured in joules per second, or watts.

$K$ is a thermal conductance in W/K, not a material thermal conductivity in
W/(m K). A conductance already represents geometry and material effects at the
chosen model scale.

---

## 5. Sign conventions

The sign conventions define the interpretation of every equation:

1. Positive current is the chosen refrigeration polarity when $\alpha>0$.
2. $Q_c>0$ means the module removes heat from the cold node.
3. $Q_h>0$ means the module delivers heat to the hot node.
4. Positive external heat enters its node.
5. Positive $VI$ means electrical power enters the module.
6. $T_h-T_c>0$ means the hot face is warmer than the cold face.

The model does not claim that positive current universally corresponds to one
named physical direction of conventional charge flow for every manufactured
module. It defines the polarity by the effective coefficient and the desired
cooling action.

---

## 6. Thermoelectric heat-rate model

The pure thermoelectric functions live in
[`thermoelectric.py`](thermoelectric.py). Their parameters are grouped in the
immutable `ThermoelectricParameters` dataclass.

### 6.1 Peltier terms

The Peltier heat rate at a face is

$$
\alpha I T.
$$

It is linear in current and uses absolute temperature. Kelvin must be used;
substituting degrees Celsius would produce the wrong Peltier magnitude.

The package evaluates the cold Peltier term at $T_c$ and the hot Peltier term
at $T_h$:

$$
\dot Q_{\mathrm{Peltier},c}=\alpha I T_c,
$$

$$
\dot Q_{\mathrm{Peltier},h}=\alpha I T_h.
$$

Reversing current reverses both Peltier terms.

### 6.2 Joule heating

Electrical resistance generates irreversible heat at the rate

$$
\dot Q_{\mathrm{Joule}}=I^2R.
$$

The simple model assigns half to each module face:

$$
\frac{1}{2}I^2R.
$$

Because current is squared, Joule heating does not reverse sign when current
reverses. It grows quadratically with current.

### 6.3 Parasitic thermal conduction

The internal heat leak is

$$
\dot Q_{\mathrm{leak}}=K(T_h-T_c).
$$

When $T_h>T_c$ and $K>0$, passive conduction carries heat from hot to cold. It
opposes refrigeration because it returns heat toward the cold node.

The word **parasitic** means that this passive conduction works against the
desired heat-pumping action. It does not mean the heat is lost from the
universe; it is transferred internally from one side to the other.

### 6.4 Cold- and hot-side heat rates

Combining the three effects gives

$$
Q_c
=\alpha I T_c
-\frac{1}{2}I^2R
-K(T_h-T_c),
$$

$$
Q_h
=\alpha I T_h
+\frac{1}{2}I^2R
-K(T_h-T_c).
$$

The cold side subtracts its Joule contribution because Joule heating reduces
the net heat the module can remove from the cold node. The hot side adds its
Joule contribution because that heat must be rejected at the hot side.

### 6.5 Voltage and electrical power

The terminal voltage is

$$
V=\alpha(T_h-T_c)+IR.
$$

The first term is the Seebeck voltage and the second is the resistive voltage.
The signed electrical power is

$$
P_{\mathrm{electrical}}=VI.
$$

### 6.6 Module energy identity

Subtracting the cold heat rate from the hot heat rate gives

$$
\begin{aligned}
Q_h-Q_c
&=\alpha I(T_h-T_c)+I^2R \\
&=I\left[\alpha(T_h-T_c)+IR\right] \\
&=VI.
\end{aligned}
$$

The module therefore rejects the heat removed from the cold side plus the
electrical power supplied to it:

$$
Q_h=Q_c+VI.
$$

This identity is checked across positive, zero, and negative current in the
test suite.

### 6.7 Zero-current limiting case

When $I=0$:

$$
Q_c=Q_h=-K(T_h-T_c).
$$

If $T_h>T_c$, both values are negative under the package sign conventions.
Negative $Q_c$ means the module is adding heat to the cold node rather than
removing it. Negative $Q_h$ means heat is leaving the hot node and entering the
module. The net physical process is ordinary hot-to-cold conduction.

The open-circuit voltage may still be nonzero:

$$
V=\alpha(T_h-T_c),
$$

but the electrical power is zero because $I=0$.

### 6.8 Why excessive current can reduce cooling

At fixed temperatures,

$$
Q_c(I)=\alpha T_c I-\frac{1}{2}RI^2-K(T_h-T_c).
$$

The useful Peltier contribution grows linearly with $I$, while the detrimental
Joule term grows quadratically. The fixed-temperature maximum occurs at

$$
I_{Q_c,\max}=\frac{\alpha T_c}{R}.
$$

Beyond this current, increasing current reduces $Q_c$ and can eventually make
$Q_c<0$. Cooling COP may begin declining before maximum cooling is reached.

### 6.9 Coefficient of performance

The cooling coefficient of performance is

$$
\mathrm{COP}=\frac{Q_c}{VI}.
$$

It is physically useful for refrigeration only when both $Q_c>0$ and $VI>0$.
At zero electrical power the ratio is undefined. The direct
`coefficient_of_performance` function raises `ZeroDivisionError`; trajectory
diagnostics use `None` at those points.

---

## 7. Two-node transient energy balances

The transient model lives in [`transient.py`](transient.py). The cold and hot
nodes store energy according to their thermal capacitances.

### 7.1 Cold node

$$
C_c\frac{dT_c}{dt}
=G_c(T_{c,\infty}-T_c)
+\dot q_{c,\mathrm{ext}}
-Q_c.
$$

The terms on the right are:

1. Heat from the cold reservoir into the cold node.
2. External heat directly entering the cold node.
3. Heat removed by the thermoelectric module.

Dividing the net heat rate in watts by $C_c$ in J/K produces a temperature
rate in K/s.

### 7.2 Hot node

$$
C_h\frac{dT_h}{dt}
=G_h(T_{h,\infty}-T_h)
+\dot q_{h,\mathrm{ext}}
+Q_h.
$$

Here positive $Q_h$ enters the hot node, so it appears with a plus sign.

### 7.3 Combined-node energy balance

Adding the two balances and using $Q_h-Q_c=VI$ gives

$$
\begin{aligned}
C_c\frac{dT_c}{dt}+C_h\frac{dT_h}{dt}
={}&G_c(T_{c,\infty}-T_c)
+G_h(T_{h,\infty}-T_h) \\
&+\dot q_{c,\mathrm{ext}}
+\dot q_{h,\mathrm{ext}}
+VI.
\end{aligned}
$$

Internal thermoelectric heat transfer cancels from the combined balance. The
stored energy of the two nodes changes only because of reservoir heat,
external heat, and electrical power.

### 7.4 Reservoir time-scale intuition

For an isolated single-node reservoir balance,

$$
C\frac{dT}{dt}=G(T_\infty-T),
$$

the ratio $C/G$ has units of seconds. It is a useful approximate response time.
The actual two-node thermoelectric dynamics are coupled, so $C_c/G_c$ and
$C_h/G_h$ are guides rather than exact system time constants.

---

## 8. Reference numerical example

The package freezes one reference experiment in
`constant_current_reference_experiment`:

| Quantity | Value |
| --- | ---: |
| $\alpha$ | 0.05 V/K |
| $R$ | 2.0 ohm |
| $K$ | 0.5 W/K |
| $C_c$ | 100 J/K |
| $C_h$ | 200 J/K |
| $G_c$ | 2.0 W/K |
| $G_h$ | 4.0 W/K |
| Initial $T_c,T_h$ | 300 K, 300 K |
| Reservoir $T_{c,\infty},T_{h,\infty}$ | 300 K, 300 K |
| Current | 1 A |
| External heat inputs | 0 W, 0 W |
| Duration | 60 s |
| RK4 step | 0.1 s |

At the initial equal-temperature state, the conduction term is zero:

$$
Q_c=0.05(1)(300)-\frac{1}{2}(1)^2(2)=14\ \mathrm{W},
$$

$$
Q_h=0.05(1)(300)+\frac{1}{2}(1)^2(2)=16\ \mathrm{W}.
$$

The reservoir terms are initially zero, so

$$
\frac{dT_c}{dt}=-\frac{14}{100}=-0.14\ \mathrm{K/s},
$$

$$
\frac{dT_h}{dt}=\frac{16}{200}=0.08\ \mathrm{K/s}.
$$

The initial voltage is 2 V and the input power is 2 W. The identity
$Q_h-Q_c=VI$ gives $16-14=2$ W.

The current RK4 implementation gives the following values after 60 s:

| Quantity | Value |
| --- | ---: |
| $T_c$ | 295.971976 K |
| $T_h$ | 302.404041 K |
| $T_h-T_c$ | 6.432065 K |
| $Q_c$ | 10.582566 W |
| $Q_h$ | 12.904170 W |
| $V$ | 2.321603 V |
| $VI$ | 2.321603 W |
| Cooling COP | 4.558301 |

The independent constant-input steady-state solver gives approximately
$T_c=295.107006$ K and $T_h=303.045731$ K. The 60 s trajectory is therefore
approaching, but has not completely reached, steady state.

These are model predictions, not measurements.

---

## 9. Code walkthrough: conventional model

### 9.1 `thermoelectric.py`: pure algebra

`ThermoelectricParameters` stores $\alpha$, $R$, and $K$. The module then
provides small pure functions:

- `peltier_heat`
- `joule_heating`
- `conductive_heat_leak`
- `cold_side_heat`
- `hot_side_heat`
- `voltage`
- `electrical_power`
- `coefficient_of_performance`

These functions do not advance time or modify state. Given the same inputs,
they return the same scalar outputs.

### 9.2 `controls.py`: current schedules

`PiecewiseConstantCurrent` represents a right-continuous schedule. If

```python
transition_times = (10.0, 30.0)
values = (0.0, 1.0, 0.0)
```

then current is 0 A before 10 s, 1 A from 10 s through the interval before
30 s, and 0 A from 30 s onward. Right-continuous means the new value applies
at the transition time itself.

Convenience constructors create:

- a constant input with `PiecewiseConstantCurrent.constant`;
- one step with `PiecewiseConstantCurrent.step`; and
- one rectangular pulse with `PiecewiseConstantCurrent.pulse`.

The class validates schedule lengths, finite values, nonnegative transition
times, and strictly increasing transitions.

### 9.3 `two_node_rhs`: instantaneous temperature rates

`two_node_rhs` performs the following sequence:

1. Evaluate $Q_c$ and $Q_h$ at the current temperatures and current.
2. Evaluate cold and hot reservoir heat transfer.
3. Add external heat inputs.
4. Construct the net heat rate for each node.
5. Divide by the corresponding thermal capacitance.
6. Return `TemperatureRates(cold, hot)` in K/s.

One RHS call does not advance time. It answers: “If the state is currently
this, what are the instantaneous temperature slopes?”

### 9.4 `integrate_two_node`: RK4 trajectory

`integrate_two_node` repeatedly calls the RHS with the classical fourth-order
Runge--Kutta method. For a coupled state $y=[T_c,T_h]$ and RHS $f(y)$:

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
k_4=f(y_n+\Delta t\,k_3),
$$

$$
y_{n+1}
=y_n+\frac{\Delta t}{6}(k_1+2k_2+2k_3+k_4).
$$

Each $k$ contains both cold and hot temperature rates. Both temperatures must
be advanced together because each face heat rate depends on both $T_c$ and
$T_h$.

The returned `TemperatureTrajectory` contains aligned immutable tuples:

```text
time = (t_0, t_1, ..., t_N)
cold = (T_c(t_0), T_c(t_1), ..., T_c(t_N))
hot  = (T_h(t_0), T_h(t_1), ..., T_h(t_N))
```

The initial and exact requested final times are always included. A final
partial step is used when duration is not an integer multiple of the requested
step.

### 9.5 RK4 at current switches

An RK4 interval never crosses a known piecewise-constant current transition.
The integrator shortens the preceding step so it ends exactly at the switch,
then begins a new step using the new current.

Within one RK4 interval, $k_1$ through $k_4$ use one held current value. This
avoids unintentionally averaging a discontinuous control across a step.

Temperatures remain continuous at a finite current switch because a finite
thermal capacitance cannot acquire finite energy instantaneously. Current,
$Q_c$, $Q_h$, voltage, power, COP, and temperature derivatives may jump.

### 9.6 `two_node_steady_state`: algebraic cross-check

For constant inputs, setting both temperature rates to zero produces a
two-by-two linear system for $T_c$ and $T_h$. `two_node_steady_state` solves
that system independently of RK4.

Thermal capacitances do not appear because steady state has no stored-energy
rate. A singular or numerically ill-conditioned system raises `ValueError`.

Comparing a long RK4 run with the algebraic result helps distinguish a correct
equilibrium from a time-stepping result that merely appears stable.

### 9.7 `diagnostics.py`: derived histories

`evaluate_trajectory` post-processes every temperature sample into aligned
histories of:

- current;
- $T_h-T_c$;
- $Q_c$;
- $Q_h$;
- terminal voltage;
- electrical power; and
- cooling COP.

Diagnostics use the right-continuous current at a switch. COP is `None` when
electrical power is zero.

### 9.8 `experiments.py`: reproducible input bundles

`TwoNodeExperiment` stores everything required to reproduce one run:

- thermoelectric parameters;
- node thermal parameters;
- initial temperatures;
- duration and time step;
- current input;
- reservoir temperatures; and
- external heat inputs.

`run_two_node_experiment` runs RK4 and then evaluates diagnostics, returning
both in `ExperimentResult`.

Keeping all inputs together prevents learned and conventional comparisons from
silently using different parameter values.

### 9.9 Minimal conventional API example

```python
from thermotwin import (
    constant_current_reference_experiment,
    run_two_node_experiment,
)

experiment = constant_current_reference_experiment()
result = run_two_node_experiment(experiment)

print(result.trajectory.cold[-1])
print(result.trajectory.hot[-1])
print(result.diagnostics.cooling_cop[-1])
```

### 9.10 Custom pulse example

```python
from dataclasses import replace

from thermotwin import (
    PiecewiseConstantCurrent,
    constant_current_reference_experiment,
    run_two_node_experiment,
)

base = constant_current_reference_experiment()
pulse = PiecewiseConstantCurrent.pulse(
    start_time=10.0,
    end_time=30.0,
    pulse_current=1.0,
    baseline_current=0.0,
)
experiment = replace(base, current=pulse)
result = run_two_node_experiment(experiment)
```

---

### 9.11 Contact-aware four-node model

The original two-node solver remains available as a reduced model without
explicit contacts. The separate
[contact_transient.py](contact_transient.py) module adds four dynamic
temperatures:

- cold thermoelectric face $T_c$;
- hot thermoelectric face $T_h$;
- cold heat exchanger $T_{x,c}$; and
- hot heat exchanger $T_{x,h}$.

The cold contact heat is positive from the cold exchanger to the cold face,
and the hot contact heat is positive from the hot face to the hot exchanger:

$$
\dot q_{\mathrm{contact},c}
=\frac{T_{x,c}-T_c}{R_{\mathrm{contact},c}},
$$

$$
\dot q_{\mathrm{contact},h}
=\frac{T_h-T_{x,h}}{R_{\mathrm{contact},h}}.
$$

The implemented energy balances are

$$
C_c\frac{dT_c}{dt}
=\dot q_{\mathrm{contact},c}-Q_c,
$$

$$
C_h\frac{dT_h}{dt}
=Q_h-\dot q_{\mathrm{contact},h},
$$

$$
C_{x,c}\frac{dT_{x,c}}{dt}
=G_c(T_{c,\infty}-T_{x,c})
+\dot q_{c,\mathrm{ext}}
-\dot q_{\mathrm{contact},c},
$$

$$
C_{x,h}\frac{dT_{x,h}}{dt}
=G_h(T_{h,\infty}-T_{x,h})
+\dot q_{h,\mathrm{ext}}
+\dot q_{\mathrm{contact},h}.
$$

Adding all four equations cancels both contact terms. Using
$Q_h-Q_c=VI$, the total stored-energy rate is

$$
\begin{aligned}
\frac{dE_{\mathrm{stored}}}{dt}
={}&G_c(T_{c,\infty}-T_{x,c})
+G_h(T_{h,\infty}-T_{x,h})\\
&+\dot q_{c,\mathrm{ext}}+\dot q_{h,\mathrm{ext}}+VI.
\end{aligned}
$$

Contact resistance therefore changes internal temperature drops and heat
delivery without creating or destroying energy. The baseline assigns separate
thermal capacitances to all four nodes and applies external loads at the
exchangers.

The four_node_contact_rhs function evaluates the four instantaneous rates.
The integrate_four_node_contact function uses the same RK4 and exact
current-transition behavior as the two-node integrator. Contact resistances
must be finite and positive. To omit contacts, use the two-node model rather
than setting a resistance to zero.

The [contact_experiments.py](contact_experiments.py) module freezes a generic
comparison case with:

| Quantity | Reference value |
| --- | ---: |
| Current | 1 A |
| Duration | 60 s |
| Time step | 0.1 s |
| Initial and reservoir temperatures | 300 K |
| Cold face and exchanger capacitances | 50, 50 J/K |
| Hot face and exchanger capacitances | 100, 100 J/K |
| Cold and hot contact resistances | 0.25, 0.25 K/W |
| External heat inputs | 0 W |

The values are a controlled generic baseline, not hardware-calibrated
properties. The paired capacitances preserve the 100 J/K cold and 200 J/K hot
totals from the reduced reference case.

The [contact_diagnostics.py](contact_diagnostics.py) module evaluates aligned
histories of:

- current;
- face and exchanger temperature differences;
- both face-to-exchanger contact drops;
- both contact heat rates;
- $Q_c$, $Q_h$, voltage, and electrical power;
- module cooling COP, $Q_c/(VI)$;
- exchanger-delivered cooling COP,
  $\dot q_{\mathrm{contact},c}/(VI)$; and
- stored-energy rate, external-energy rate, and their closure residual.

Module and exchanger-delivered COP differ during a transient because the cold
face has thermal capacitance:

$$
\dot q_{\mathrm{contact},c}-Q_c
=C_c\frac{dT_c}{dt}.
$$

The 60 s reference gives approximately:

| Output | Value |
| --- | ---: |
| Final cold TE face | 294.795190 K |
| Final cold exchanger | 296.735891 K |
| Final hot TE face | 303.959316 K |
| Final hot exchanger | 301.743400 K |
| Final cold contact drop | 1.940701 K |
| Final hot contact drop | 2.215916 K |
| Final cold contact heat | 7.762803 W |
| Final hot contact heat | 8.863664 W |
| Final module cooling COP | 3.725357 |
| Final exchanger-delivered cooling COP | 3.157914 |
| Maximum energy-closure residual | below $5\times10^{-15}$ W |

The [contact_report.py](contact_report.py) module compares the four temperature
histories against the reduced two-node trajectory, plots both contact drops,
compares module and delivered heat rates, and sweeps equal cold/hot contact
resistances through 0.1, 0.25, 0.5, and 1.0 K/W.

For this fixed 60 s experiment, increasing resistance increases both contact
drops, decreases heat removed from the cold exchanger, makes the TE-face
temperatures more extreme, and leaves the exchanger temperatures closer to the
reservoir. These are results for the stated controlled conditions, not a proof
of universal monotonic behavior.

Minimal use:

~~~python
from thermotwin import (
    constant_current_contact_reference_experiment,
    run_four_node_contact_experiment,
)

experiment = constant_current_contact_reference_experiment()
result = run_four_node_contact_experiment(experiment)

print(result.trajectory.cold_face[-1])
print(result.trajectory.cold_exchanger[-1])
print(result.diagnostics.cold_contact_heat[-1])
print(result.diagnostics.exchanger_cooling_cop[-1])
~~~

The four-node derivation exercises are in
[notes/10_contact_aware_transient.md](notes/10_contact_aware_transient.md).
The frozen experiment, diagnostics, energy-closure, COP, topology-comparison,
and sweep exercises are in
[notes/11_contact_reference_diagnostics.md](notes/11_contact_reference_diagnostics.md).

### 9.12 Ideal virtual test stand

The conventional solvers expose every stored RK4 state, but experimental
inference should only receive values that defined sensors measured at defined
times. The [virtual_test_stand.py](virtual_test_stand.py) module provides this
observation boundary without changing the four-node physics.

The first ideal test stand has four named temperature sensors:

| Sensor name | Modeled location |
| --- | --- |
| `cold_face_sensor` | cold TE face |
| `hot_face_sensor` | hot TE face |
| `cold_exchanger_sensor` | cold exchanger |
| `hot_exchanger_sensor` | hot exchanger |

Sensor name and modeled location are stored separately. A name identifies an
instrument, while the location identifies which state it observes. Names must
be unique, but the schema permits multiple named sensors at one location for a
future redundant-sensor experiment.

Each `TemperatureObservation` is one long-form reading with:

- time in seconds;
- sensor name;
- modeled node location;
- temperature in kelvin; and
- the current in amperes at that time.

`ObservationDataset` also stores the sensor definitions, requested sampling
interval, and explicit unit strings. It validates that records are ordered by
time, have no duplicate reading for one sensor at one time, reference known
sensors, and use the location declared by each sensor.

The baseline truth trajectory has 601 stored times at a 0.1 s RK4 step. The
ideal sensors request measurements every 1 s from 0 through 60 s, producing 61
measurement times. With four sensors, the long-form dataset has 244 records.
The dataset does not contain the dense truth trajectory.

`regular_measurement_times` keeps numerical and measurement resolution
separate and always includes the exact experiment end. If the duration is not
an integer multiple of the interval, the final measurement interval is
shortened. `observe_contact_trajectory` returns an exact stored value when
times align and otherwise linearly interpolates between adjacent RK4 states.
Interpolation is an observation-layer approximation, not a replacement for
time-step convergence of the physical solver.

Current is evaluated at every measurement time with the same right-continuous
convention as the integrator. At a scheduled switch the newly commanded
current is recorded immediately, while finite-capacitance node temperatures
remain continuous.

Minimal use:

~~~python
from thermotwin import run_ideal_contact_reference_test_stand

dataset = run_ideal_contact_reference_test_stand()

print(dataset.measurement_times[:3])
print(len(dataset.measurement_times))
print(len(dataset.observations))
print(dataset.observations_for("cold_face_sensor")[-1])
~~~

The baseline deliberately has exact sensors with no noise, bias, lag, missing
readings, or calibration error. All four locations are observed first to
validate the data path. Later identifiability studies can hide selected
sensors without changing the truth solver.

The companion exercises are in
[notes/12_virtual_test_stand.md](notes/12_virtual_test_stand.md).

### 9.13 Reproducible Gaussian temperature noise

The ideal dataset is the limiting case against which measurement effects are
checked. The separate [measurement_noise.py](measurement_noise.py) module
creates a new noisy dataset without modifying that ideal input.

`GaussianTemperatureNoise` defines:

- one default temperature-error standard deviation in kelvin;
- optional named per-sensor standard-deviation overrides; and
- an integer random seed.

All standard deviations must be finite and nonnegative. Override names must be
unique and must refer to sensors in the dataset. The frozen generic learning
case uses

~~~text
independent Gaussian temperature errors
mean = 0 K
standard deviation = 0.05 K
random seed = 2026
~~~

These are controlled synthetic settings, not specifications or calibration
results for real sensors. The initial model assumes errors are independent
between sensors and times, have the same distribution at every operating
condition, and affect only temperature. It does not perturb current, time, or
sensor labels.

`apply_gaussian_temperature_noise` returns a `TemperatureNoiseResult` holding
the noisy `ObservationDataset` and the exact configuration used to produce
it. It does not include the ideal dataset or dense truth. Because all records
are immutable, callers can retain the ideal dataset separately for validation
without the noise function altering it.

For the 244-reading seed-2026 baseline, the realized temperature errors have
approximately:

| Statistic | Realized value |
| --- | ---: |
| Mean error | -0.003400 K |
| RMS error | 0.051830 K |
| Maximum absolute error | 0.187827 K |

The realized finite-sample mean is not exactly zero. Zero mean describes the
generating distribution; any finite trial has sampling variation. Repeated
trials require different recorded seeds.

Minimal use:

~~~python
from thermotwin import (
    GaussianTemperatureNoise,
    run_noisy_contact_reference_test_stand,
)

noise = GaussianTemperatureNoise(
    default_standard_deviation=0.05,
    random_seed=2026,
    sensor_standard_deviations=(("cold_face_sensor", 0.10),),
)
result = run_noisy_contact_reference_test_stand(noise_model=noise)

print(result.noise_model)
print(result.dataset.observations[:4])
~~~

Setting every standard deviation to zero exactly reproduces the ideal
temperature readings. This limiting case checks that the transformation adds
only the intended measurement effect.

### 9.14 Fixed per-sensor temperature bias

Random noise and systematic bias represent different measurement errors. The
[measurement_bias.py](measurement_bias.py) module defines a constant additive
offset for each sensor:

$$
T_{\mathrm{observed},s}(t)
=T_{\mathrm{input},s}(t)+b_s.
$$

`FixedTemperatureBias` stores one default offset in kelvin and optional named
per-sensor overrides. Biases may be positive, negative, or zero, but must be
finite. Override names must be unique and must refer to sensors in the input
dataset.

The frozen generic learning baseline uses:

| Sensor | Fixed bias |
| --- | ---: |
| Cold face | +0.10 K |
| Hot face | 0 K |
| Cold exchanger | 0 K |
| Hot exchanger | 0 K |

This deliberately isolates one systematic error. It is not a measured
calibration offset. At all 61 cold-face measurement times, the bias-only
reading is exactly 0.10 K above ideal truth. Averaging those errors still gives
0.10 K, unlike independent zero-mean noise whose sample mean tends toward zero
as the sample count increases.

`apply_fixed_temperature_bias` returns a new `TemperatureBiasResult` and does
not alter the input dataset. It preserves times, current, sensor definitions,
locations, units, ordering, and record count. A zero-bias model exactly
reproduces the input readings.

The high-level `run_noisy_biased_contact_reference_test_stand` workflow applies
Gaussian noise followed by fixed bias and returns a
`NoisyBiasedTemperatureResult`. That result retains both configurations but
does not expose ideal truth. Because both implemented effects are additive,
reversing their order agrees to floating-point precision. Future lag and
missing-data effects will not generally commute this way.

Minimal bias-only use:

~~~python
from thermotwin import run_biased_contact_reference_test_stand

result = run_biased_contact_reference_test_stand()
print(result.bias_model)
print(result.dataset.observations_for("cold_face_sensor")[-1])
~~~

Combined noise-and-bias use:

~~~python
from thermotwin import run_noisy_biased_contact_reference_test_stand

result = run_noisy_biased_contact_reference_test_stand()
print(result.noise_model)
print(result.bias_model)
print(len(result.dataset.observations))
~~~

### 9.15 First-order dynamic sensor lag

Noise and fixed bias alter reported values instantaneously. Dynamic lag adds
sensor memory. For sensor $s$, the continuous first-order model is

$$
\tau_s\frac{dT_{m,s}}{dt}=T_{\mathrm{input},s}-T_{m,s},
$$

where $T_{m,s}$ is the reported sensor state, $T_{\mathrm{input},s}$ is the
modeled node temperature, and $\tau_s$ is the time constant in seconds. The
implemented interval update treats the current input temperature as the
relaxation target:

$$
a=\exp\left(-\frac{\Delta t}{\tau_s}\right),
$$

$$
T_{m,s,k}=aT_{m,s,k-1}+(1-a)T_{\mathrm{input},s,k}.
$$

The first reported state is initialized to the first input temperature. A
zero time constant bypasses the recurrence and reproduces the input exactly.
For constant input, any initial difference decays exponentially. Actual time
differences are used, so irregularly spaced records are supported.

`FirstOrderTemperatureLag` stores a nonnegative finite default time constant
and optional named per-sensor overrides. The frozen generic baseline is:

| Sensor | Time constant |
| --- | ---: |
| Cold face | 2 s |
| Hot face | 0 s |
| Cold exchanger | 0 s |
| Hot exchanger | 0 s |

These values create an isolated learning case and are not calibrated sensor
properties. A larger time constant makes the cold-face reading respond more
slowly.

The high-level reference workflow calculates lag on the dense 0.1 s ideal
signal before sampling the output every 1 s. Consequently, asking for 5 s
output produces the same lagged values at common times as selecting every
fifth value from the 1 s output. Filtering only after coarse downsampling would
make sensor dynamics depend artificially on the logging interval.

For the frozen cooling transient:

| Quantity | Value |
| --- | ---: |
| Initial cold-face lag error | 0 K |
| Cold-face error at 1 s | +0.204232 K |
| Maximum cold-face lag error | +0.376595 K near 4 s |
| Final ideal cold face | 294.795190 K |
| Final lagged cold face | 294.853072 K |
| Final cold-face lag error | +0.057882 K |

The positive error means the lagged sensor remains warmer while its node is
cooling. The error shrinks later because the physical temperature changes more
slowly. The other three sensors remain identical to ideal in this baseline.

`run_lagged_noisy_biased_contact_reference_test_stand` applies effects in this
order:

~~~text
dense node truth -> sensor lag -> output sampling -> fixed bias -> random noise
~~~

The returned `LaggedNoisyBiasedTemperatureResult` retains all three
configurations without exposing ideal truth. Random measurement noise is added
after lag rather than being smoothed by the lag filter.

This lag is an observation filter only. It assumes the physical sensor does
not draw enough heat to change the modeled node temperature. Representing
sensor mass and thermal contact as part of the physical network would require
additional thermal states and coupling terms.

Minimal use:

~~~python
from thermotwin import (
    run_lagged_contact_reference_test_stand,
    run_lagged_noisy_biased_contact_reference_test_stand,
)

lag_only = run_lagged_contact_reference_test_stand()
all_effects = run_lagged_noisy_biased_contact_reference_test_stand()

print(lag_only.lag_model)
print(all_effects.bias_model)
print(all_effects.noise_model)
~~~

The consolidated measurement-imperfection exercises are in
[notes/13_measurement_imperfections.md](notes/13_measurement_imperfections.md).
They cover sampling, noise, bias, lag, transformation order, and missing
observations.

### 9.16 Deterministic missing observations

A missing observation means that no usable sensor record is available. It is
not a temperature of 0 K, and the current implementation does not insert a
`NaN` or invent an interpolated replacement. Instead, the unavailable
long-form row is omitted.

`TemperatureSensorOutage` defines one inclusive interval using:

- a nonempty sensor name;
- a finite, nonnegative start time; and
- a finite, nonnegative end time that does not precede the start.

`DeterministicTemperatureMissingness` stores zero or more outage intervals.
Overlapping inclusive intervals for the same sensor are rejected because they
are redundant and make provenance ambiguous. Outages for different sensors
may overlap. Named sensors are checked against the input dataset when the
transformation is applied.

Let $\mathcal O_s$ be the outage intervals configured for sensor $s$. A record
at time $t_k$ is retained only if

$$
t_k\notin[o^{\mathrm{start}},o^{\mathrm{end}}]
\quad\text{for every }o\in\mathcal O_s.
$$

The interval endpoints are inclusive. Comparisons use a small floating-point
tolerance so a nominal boundary such as 0.3 s behaves correctly even when a
stored floating-point time is represented as 0.30000000000000004 s.

The generic learning baseline is a communication outage for
`cold_face_sensor` from 20 through 30 s. With 1 s measurements, the removed
times are

~~~text
20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30 s
~~~

Therefore:

| Quantity | Complete data | After outage |
| --- | ---: | ---: |
| Unique experiment times | 61 | 61 |
| Cold-face records | 61 | 50 |
| Each other sensor's records | 61 | 61 |
| Total records | 244 | 233 |

The full dataset retains all 61 times because at least three sensors still
report during the outage. The cold-face sensor remains in sensor metadata even
though its observation history is shorter. This long-form representation does
not require a rectangular sensor-by-time table.

`apply_deterministic_temperature_missingness` returns a new dataset containing
the original retained observation objects. It preserves sensor definitions,
sampling interval, and units. Zero outage intervals are the exact no-effect
limit. An outage outside the experiment also has no effect. Removing every
record is rejected because `ObservationDataset` must remain nonempty.

Missingness is an observation transformation only. It does not change the
four-node thermal trajectory, contact heat transfer, current schedule, or the
unavailable sensor's internal lag state. In the complete reference workflow,
the order is:

~~~text
dense node truth
    -> first-order sensor lag
    -> output sampling
    -> fixed sensor bias
    -> independent Gaussian noise
    -> deterministic record removal
~~~

Noise is generated before the unavailable rows are removed. This preserves
the seeded noise values of later retained records and represents a sensor that
formed readings but failed to transmit selected records. A sensor that was
powered off and did not update its state would require a different model.

Minimal missing-only use:

~~~python
from thermotwin import run_missing_contact_reference_test_stand

missing_only = run_missing_contact_reference_test_stand()
print(len(missing_only.dataset.observations))
print(missing_only.missingness_model)
~~~

Complete measurement-pipeline use:

~~~python
from thermotwin import run_incomplete_contact_reference_test_stand

result = run_incomplete_contact_reference_test_stand()
print(result.lag_model)
print(result.bias_model)
print(result.noise_model)
print(result.missingness_model)
print(len(result.dataset.observations))
~~~

This first model describes a known deterministic outage. It does not yet
represent random packet loss, value-dependent failure, sensor-health states,
imputation, or a calibrated hardware missingness mechanism.

### 9.17 Self-contained dataset provenance and quality audit

The measurement modules previously retained individual transformation
configurations in their result wrappers. Generated observation tables now also
carry a consistent `DatasetProvenance` record. This closes an important gap:
an evaluation dataset can state its ground truth and how it was produced
without including the dense trajectory that an inference method must not see.

The provenance contains a `ContactExperimentMetadata` object with:

- experiment and regime names;
- the `train`, `validation`, `test`, or `unsplit` assignment;
- all three thermoelectric parameters;
- all eight four-node thermal parameters;
- all four initial temperatures;
- both reservoir temperatures and external heat inputs;
- duration and RK4 integration time step; and
- the scalar or complete piecewise-constant current schedule.

`ContactExperimentMetadata.to_experiment()` reconstructs the recorded
`FourNodeContactExperiment`. This is a configuration/ground-truth record, not
a stored solution. `ObservationDataset` still has no dense `trajectory` or
`truth` attribute.

Provenance also contains ordered `ObservationProcessStep` records. For the
combined incomplete baseline, the order is:

~~~text
ideal dense sampling
-> first-order temperature lag
-> output sampling
-> fixed temperature bias
-> Gaussian temperature noise
-> deterministic temperature missingness
~~~

Each applied step stores its actual settings. The Gaussian step records the
random seed and standard deviations. Lag and bias record defaults and named
sensor overrides. Every outage records its sensor and inclusive start/end
times. Transformations that have no effect preserve the exact input dataset;
their configuration remains available in the result wrapper.

Minimal provenance inspection:

~~~python
from thermotwin import run_incomplete_contact_reference_test_stand

result = run_incomplete_contact_reference_test_stand()
provenance = result.dataset.provenance

print(provenance.experiment.regime_name)
print(provenance.experiment.thermal_parameters.cold_contact_resistance)
print(tuple(step.name for step in provenance.observation_steps))
reconstructed_experiment = provenance.experiment.to_experiment()
~~~

The separate [dataset_quality.py](dataset_quality.py) module calculates a
deterministic summary for one dataset or a collection. For each dataset it
reports:

- observed and expected records;
- total and per-sensor missing counts;
- completeness fraction;
- observed and expected measurement-time counts;
- temperature and current ranges;
- provenance and ground-truth availability; and
- ordered observation-process names.

For a collection it additionally verifies unique regime names and the presence
of whole training, validation, and test regimes. Run the frozen report with:

~~~bash
python3 -m thermotwin.dataset_quality
~~~

The current ideal split contains three entire experiments, 732 observed of 732
expected records, complete provenance and physical truth, and one distinct
training, validation, and test regime. All quality gates pass. The controlled
20--30 s cold-face outage separately reports 233 of 244 records: exactly 11
missing cold-face readings and no invented replacement values.

The quality audit verifies schema and provenance. It does not prove that the
synthetic physics matches hardware, that a noise distribution is realistic, or
that a parameter is identifiable.

---

## 10. Forward physics-informed neural network

The forward PINN lives in [`forward_pinn.py`](forward_pinn.py). It solves the
same two-node initial-value problem as RK4, but represents the complete
temperature trajectory with a neural network.

### 10.1 Inputs, outputs, and fixed quantities

The network input is time $t$. Its two outputs are $T_c(t)$ and $T_h(t)$.

The first forward problem does not learn $\alpha$, $R$, $K$, $C_c$, $C_h$,
$G_c$, or $G_h$. All physical parameters and experimental inputs are fixed.
This is why it is a forward problem rather than an inverse problem.

### 10.2 Architecture

The default architecture is:

```text
time → 32 tanh units → 32 tanh units → 2 raw outputs
```

Tanh is smooth, which is important because the physics loss requires time
derivatives of the outputs.

### 10.3 Time normalization

Raw time from 0 to $t_{\mathrm{end}}$ is mapped to approximately $[-1,1]$:

$$
\tau=2\frac{t}{t_{\mathrm{end}}}-1.
$$

The network receives $\tau$, while automatic differentiation applies the chain
rule to calculate derivatives with respect to physical time $t$.

### 10.4 Exact initial conditions

The raw network outputs $N_c(t)$ and $N_h(t)$ are transformed as

$$
T(t)=T(0)
+\frac{t}{t_{\mathrm{end}}}
T_{\mathrm{scale}}N(t).
$$

At $t=0$, the learned contribution is exactly zero for any network weights.
Both initial temperatures are therefore enforced exactly instead of being
encouraged through a soft initial-condition penalty.

The transformation does not force the initial slope to zero. Differentiating
it produces both a raw-output term and a raw-output-derivative term.

`temperature_scale` is a numerical output scale, not a new physical property.

### 10.5 Automatic differentiation and residuals

PyTorch automatic differentiation computes the network derivatives
$dT_c/dt$ and $dT_h/dt$. The residuals are

$$
r_c
=\left(\frac{dT_c}{dt}\right)_{\mathrm{network}}
-\frac{G_c(T_{c,\infty}-T_c)
+\dot q_{c,\mathrm{ext}}-Q_c}{C_c},
$$

$$
r_h
=\left(\frac{dT_h}{dt}\right)_{\mathrm{network}}
-\frac{G_h(T_{h,\infty}-T_h)
+\dot q_{h,\mathrm{ext}}+Q_h}{C_h}.
$$

Both residuals have units of K/s. A physically consistent solution makes them
zero throughout the time domain.

### 10.6 Collocation points and loss

The default model evaluates the residuals at 128 uniformly spaced collocation
points. These are time coordinates, not labeled temperature observations.

The forward loss is

$$
\mathcal L_{\mathrm{forward}}
=\mathrm{mean}(r_c^2)
+\mathrm{mean}(r_h^2).
$$

RK4 temperatures are not used in training. This separation makes RK4 a genuine
post-training numerical comparison rather than hidden supervision.

### 10.7 Default forward configuration

| Setting | Default |
| --- | ---: |
| Hidden layers | 2 |
| Hidden width | 32 |
| Collocation points | 128 |
| Epochs | 2,000 |
| Adam learning rate | $10^{-3}$ |
| Temperature scale | 10 K |
| Random seed | 7 |
| Device | CPU |

`device="mps"` requests Apple Metal acceleration and raises an error when MPS
is unavailable. `device="auto"` chooses MPS when available and otherwise uses
CPU. CPU is the default because this first model is small.

### 10.8 Forward validation results

For the reference problem, the current default CPU run gives approximately:

| Metric | Value |
| --- | ---: |
| Final physics loss | $6.55\times10^{-7}$ K$^2$/s$^2$ |
| Cold RMSE versus RK4 | 0.002747 K |
| Hot RMSE versus RK4 | 0.001683 K |
| Cold maximum absolute error | 0.004788 K |
| Hot maximum absolute error | 0.002847 K |

Results can vary slightly across PyTorch versions and hardware even with a
fixed seed.

### 10.9 Comparison report

[`forward_pinn_report.py`](forward_pinn_report.py) creates four panels:

1. RK4 and PINN temperature trajectories.
2. Pointwise PINN-minus-RK4 temperature errors.
3. Cold and hot physics residuals across time.
4. Training loss versus epoch on a logarithmic scale.

RMSE alone can hide localized errors. The error and residual panels show where
the approximation is weakest, including behavior near interval endpoints.

### 10.10 Current forward-PINN restriction

The first forward PINN accepts constant current only. The conventional RK4
solver already supports steps and pulses, but a rectangular switch causes a
temperature-derivative discontinuity. A single smooth neural network may have
difficulty representing that discontinuity precisely.

The separate piecewise contact PINN in Sections 10.18 through 10.22 now uses
the first option: it splits the time domain at every current switch. The
original two-node PINN deliberately remains the smaller constant-current
baseline.

### 10.11 Contact-aware forward PINN

[`contact_forward_pinn.py`](contact_forward_pinn.py) is a separate learned
solver for the explicit-contact four-node topology. It does not replace or
silently alter the two-node PINN. The two learned forward models now answer
different modeling questions:

| Model | Learned temperature functions | Explicit contacts | Current support |
| --- | --- | --- | --- |
| `ForwardPINN` | $T_c(t), T_h(t)$ | No | Constant |
| `ContactForwardPINN` | $T_{cf}(t), T_{hf}(t), T_{cx}(t), T_{hx}(t)$ | Yes | Constant |
| `PiecewiseContactForwardPINN` | Four temperatures per segment | Yes | Piecewise constant |

Here `f` means thermoelectric face and `x` means heat exchanger. Both models
are forward PINNs: every physical coefficient is supplied and fixed. Neither
one infers a parameter at this stage.

### 10.12 Four-output architecture and exact initial state

The contact model uses the same CPU-first default depth and width as the first
PINN, but its final layer has four outputs:

~~~text
time -> 32 tanh units -> 32 tanh units -> 4 raw outputs
~~~

The output columns have one fixed order throughout the module:

~~~text
cold face, hot face, cold exchanger, hot exchanger
~~~

For each state $j$, the transformed output is

$$
T_j(t)=T_j(0)
+\frac{t}{t_{\mathrm{end}}}T_{\mathrm{scale}}N_j(t).
$$

This makes all four values at $t=0$ exact for every possible set of network
weights. The initial derivatives remain trainable. In the frozen experiment,
all four initial values are 300 K.

### 10.13 Contact-aware physics residuals

The network temperatures first define contact heat rates:

$$
\dot q_{cc}=\frac{T_{cx}-T_{cf}}{R_{cc}},
\qquad
\dot q_{hc}=\frac{T_{hf}-T_{hx}}{R_{hc}}.
$$

The thermoelectric $Q_c$ and $Q_h$ functions use $T_{cf}$ and $T_{hf}$, not
the exchanger temperatures. Automatic differentiation gives the four network
temperature rates. The residuals are the network rates minus the rates
required by the four energy balances:

$$
r_{cf}=\left(\frac{dT_{cf}}{dt}\right)_{\mathrm{network}}
-\frac{\dot q_{cc}-Q_c}{C_{cf}},
$$

$$
r_{hf}=\left(\frac{dT_{hf}}{dt}\right)_{\mathrm{network}}
-\frac{Q_h-\dot q_{hc}}{C_{hf}},
$$

$$
r_{cx}=\left(\frac{dT_{cx}}{dt}\right)_{\mathrm{network}}
-\frac{G_c(T_{c,\infty}-T_{cx})
+\dot q_{c,\mathrm{ext}}-\dot q_{cc}}{C_{cx}},
$$

$$
r_{hx}=\left(\frac{dT_{hx}}{dt}\right)_{\mathrm{network}}
-\frac{G_h(T_{h,\infty}-T_{hx})
+\dot q_{h,\mathrm{ext}}+\dot q_{hc}}{C_{hx}}.
$$

Every residual has units K/s. The cold and hot contact heat rates appear with
opposite signs on their two adjacent nodes, so a contact transfers energy but
does not create it.

The training objective is

$$
\mathcal L_{\mathrm{contact}}
=\mathrm{mean}(r_{cf}^2)
+\mathrm{mean}(r_{hf}^2)
+\mathrm{mean}(r_{cx}^2)
+\mathrm{mean}(r_{hx}^2).
$$

All four terms currently have equal numerical weight. This is reasonable for
the frozen example because they share units and comparable scales, but it is a
modeling choice rather than a universal rule.

### 10.14 What training sees

Training sees:

1. The 128 collocation times between 0 and 60 s.
2. The known physical parameters and experimental inputs.
3. The four exact initial temperatures through the output transform.
4. The four differential-equation residuals.

Training does not see any RK4 temperature sample. After training, the learned
trajectory is evaluated at all 601 RK4 times. This keeps the conventional
solution as an independent numerical reference for the same equations.

The first contact PINN deliberately rejects switching current. That restriction
matches the smooth first two-node PINN and avoids asking one smooth network to
represent derivative discontinuities before the four-state architecture has
been validated.

### 10.15 Default contact-PINN configuration

| Setting | Default |
| --- | ---: |
| Hidden layers | 2 |
| Hidden width | 32 |
| Output temperatures | 4 |
| Collocation points | 128 |
| Epochs | 3,000 |
| Adam learning rate | $10^{-3}$ |
| Temperature scale | 10 K |
| Random seed | 11 |
| Device | CPU |

As with the two-node PINN, `device="mps"` requests Apple Metal and
`device="auto"` uses it when available. CPU remains the documented default
because this network is small and the reproducible run is practical on an
M1 MacBook Pro.

### 10.16 Frozen validation result and report

Run the complete training and report workflow from the repository root:

~~~bash
python3 -m thermotwin.contact_forward_pinn_report
~~~

With the frozen seed and reference experiment, the current default CPU run
produces:

| Metric | Value |
| --- | ---: |
| Initial physics loss | $3.282427\times10^{-1}$ K$^2$/s$^2$ |
| Final physics loss | $1.134535\times10^{-4}$ K$^2$/s$^2$ |
| Cold-face RMSE | 0.024984 K |
| Hot-face RMSE | 0.003482 K |
| Cold-exchanger RMSE | 0.015086 K |
| Hot-exchanger RMSE | 0.004939 K |

Small changes are possible across PyTorch versions and hardware. These errors
compare two numerical solution methods for the same assumed equations; they
do not validate those equations against hardware.

[`contact_forward_pinn_report.py`](contact_forward_pinn_report.py) creates six
panels:

1. Face-temperature histories from RK4 and the PINN.
2. Exchanger-temperature histories from RK4 and the PINN.
3. All four pointwise PINN-minus-RK4 errors.
4. All four ODE residual histories.
5. Cold and hot contact temperature drops from both methods.
6. Physics loss against training epoch.

The report is written by default to the ignored generated-output directory as
`thermotwin/figures/contact_forward_pinn_comparison.png`.

### 10.17 Why this comes before inverse contact inference

This stage isolates the new difficulty introduced by topology. It verifies
that one differentiable model can represent four coupled temperature states
and satisfy all four balances while the contact resistances are known. The
later inverse-contact baseline makes the cold contact resistance trainable and
adds observation mismatch to the loss. The piecewise forward stage then adds
switched current without simultaneously adding inverse optimization. These
separate baselines make the piecewise inverse implementation easier to
diagnose.

The learning worksheet is
[`notes/15_contact_forward_pinn.md`](notes/15_contact_forward_pinn.md).

### 10.18 Why switched current needs a piecewise PINN

The conventional contact solver accepts piecewise-constant current. Consider
the established pulse:

~~~text
0 <= t < 5 s:    I = 0 A
5 <= t < 20 s:   I = 1 A
20 <= t <= 60 s: I = 0 A
~~~

At 5 s and 20 s, current changes instantaneously in the idealized input. The
Peltier terms change in proportion to $I$, and Joule heating changes in
proportion to $I^2$. Consequently, $Q_c$, $Q_h$, and the temperature rates can
jump at a switch.

The temperatures themselves cannot jump in this lumped-capacitance model. A
finite thermal capacitance would require an impulse of energy to create an
instantaneous finite temperature change, and the specified current pulse does
not supply such an impulse. The physical requirements are therefore:

- four continuous temperature histories;
- potentially discontinuous left- and right-side temperature derivatives;
- a well-defined convention for the current value exactly at a switch.

A standard multilayer perceptron with smooth `tanh` activations produces one
globally smooth function. It can approximate a sharp rate change, but it
cannot represent a true derivative jump exactly. The optional
[`piecewise_contact_forward_pinn.py`](piecewise_contact_forward_pinn.py)
module instead gives each constant-current interval its own smooth
subnetwork.

### 10.19 Segment architecture and exact temperature continuity

For segment $m$, starting at $a_m$ and ending at $b_m$, define the local
progress

$$
s_m(t)=\frac{t-a_m}{b_m-a_m}.
$$

Each subnetwork predicts four unconstrained outputs $N_m(t)$. Its physical
temperature output is

$$
\mathbf T_m(t)
=\mathbf T_m(a_m)
+s_m(t)T_{\mathrm{scale}}\mathbf N_m(t).
$$

Because $s_m(a_m)=0$, every segment begins exactly at its supplied start
state, independent of its weights. The first segment uses the specified
initial temperatures. Every later start state is the previous subnetwork's
predicted endpoint:

$$
\mathbf T_m(a_m)=\mathbf T_{m-1}(b_{m-1}).
$$

Thus temperature continuity is a construction, not a soft loss penalty. The
four boundary jumps reported by the implementation are identically zero up to
floating-point arithmetic. Gradients still flow backward through each chained
endpoint, so a later segment can influence how an earlier segment ends.

The subnetworks do not share weights. Their derivatives at a common boundary
are therefore free to differ, which is exactly what the switched-current
physics permits.

### 10.20 Current convention and collocation points

The PINN uses the same right-continuous current convention as the conventional
solver. At exactly 5 s the active value is 1 A, and at exactly 20 s it is 0 A.
The model also routes a query at a switch to the segment on its right.

An ordinary differential equation with a discontinuous right-hand side does
not have one classical derivative at the switch itself. Training collocation
points therefore exclude the transition times. The implementation allocates
the requested total number of points approximately in proportion to each
segment's duration and uses interval midpoints rather than endpoints. Every
positive-duration segment receives at least two points.

The report may evaluate a residual at a transition for visualization. That
value is explicitly the right-side residual, using the right-side subnetwork
and right-continuous current. It is not a claim that the two-sided derivative
exists there.

### 10.21 Training data and loss

The four contact residual equations remain exactly those in Section 10.13.
The important implementation change is that the residual function can now
receive one known current value per collocation time. Omitting that tensor
preserves the original constant-current behavior.

Training sees only:

1. midpoint collocation times inside the three intervals;
2. the known pulse schedule;
3. all fixed physical parameters and boundary inputs;
4. the exact initial state; and
5. the four differential-equation residuals.

No RK4 temperature is used as a target. The loss remains the sum of the four
mean-squared rate residuals, now evaluated with the scheduled current in each
segment. The dense RK4 trajectory is generated only after training for an
independent same-equation comparison.

### 10.22 Frozen switched-current validation

The default CPU-first configuration is:

| Setting | Default |
| --- | ---: |
| Current intervals | 3 |
| Hidden layers per interval | 2 |
| Hidden width | 32 |
| Outputs per interval | 4 |
| Total collocation points | 192 |
| Epochs | 5,000 |
| Adam learning rate | $10^{-3}$ |
| Temperature scale | 10 K |
| Random seed | 17 |
| Device | CPU |

Run the frozen comparison with:

~~~bash
python3 -m thermotwin.piecewise_contact_forward_pinn_report
~~~

The reference solver splits RK4 steps at both current transitions. With the
frozen configuration, the current CPU result is:

| Metric | Value |
| --- | ---: |
| Initial physics loss | $2.863935$ K$^2$/s$^2$ |
| Final physics loss | $3.863221\times10^{-5}$ K$^2$/s$^2$ |
| Maximum constructed boundary-temperature jump | 0 K |
| Cold-face RMSE | 0.008862 K |
| Hot-face RMSE | 0.001989 K |
| Cold-exchanger RMSE | 0.009327 K |
| Hot-exchanger RMSE | 0.004628 K |

Small numerical changes can occur across PyTorch versions and hardware. The
report shows face and exchanger trajectories, the right-continuous current,
pointwise errors, right-side residuals, and training loss. It is written to
`thermotwin/figures/piecewise_contact_forward_pinn_comparison.png` by default.

This result validates a fixed-parameter forward architecture for known
switched current. It does not infer contact resistance from the pulse, model a
finite electrical current rise time, or validate the equations against
hardware. Section 11.18 makes the cold contact resistance trainable while
preserving the same segmented representation and limiting cases.

The combined physics-and-code worksheet is
[`notes/17_piecewise_contact_forward_pinn.md`](notes/17_piecewise_contact_forward_pinn.md).

---

## 11. Inverse parameter baselines

The first inverse PINN implementation lives in
[`inverse_thermal_conductance.py`](inverse_thermal_conductance.py).
The companion learning exercises are in
[`notes/09_inverse_thermal_conductance.md`](notes/09_inverse_thermal_conductance.md).

### 11.1 Forward versus inverse

In the forward PINN, every physical parameter is known and the network learns
only the temperature functions.

In the first inverse PINN, the temperature functions and one physical
parameter, $K$, are learned jointly from:

1. The two energy-balance residuals.
2. Sparse temperature observations.

All other parameters are treated as exactly known.

### 11.2 Synthetic observations

The current baseline uses the RK4 reference trajectory as synthetic truth.
Temperatures are sampled every 5 s:

```text
0, 5, 10, ..., 55, 60 s
```

This produces 13 paired observations of $T_c$ and $T_h$. They contain no noise.
The dense 0.1 s RK4 trajectory remains reserved for final validation.

### 11.3 Why $K$ can affect the data

$K$ appears through

$$
K(T_h-T_c).
$$

When $T_h-T_c$ grows, larger $K$ produces a stronger passive hot-to-cold heat
leak. The temperature separation therefore carries information about $K$.

At the initial equal-temperature state, this term is zero. The experiment must
develop a nonzero temperature difference before it becomes informative about
$K$.

### 11.4 Positive parameterization

The optimizer updates an unconstrained raw scalar $k_{\mathrm{raw}}$. The
physical conductance is

$$
K=\mathrm{softplus}(k_{\mathrm{raw}})
=\log\left(1+e^{k_{\mathrm{raw}}}\right).
$$

This transformation keeps $K$ positive while allowing ordinary gradient-based
optimization. The default physical initial guess is 0.2 W/K; the synthetic
truth is 0.5 W/K.

### 11.5 Inverse losses and scaling

The residual component is normalized by 0.1 K/s:

$$
\mathcal L_{\mathrm{physics}}
=\mathrm{mean}\left[\left(\frac{r_c}{0.1\ \mathrm{K/s}}\right)^2\right]
+\mathrm{mean}\left[\left(\frac{r_h}{0.1\ \mathrm{K/s}}\right)^2\right].
$$

The observation component is normalized by 1 K:

$$
\mathcal L_{\mathrm{obs}}
=\mathrm{mean}\left[
\left(\frac{T_{\mathrm{network}}-T_{\mathrm{observed}}}{1\ \mathrm{K}}\right)^2
\right].
$$

The baseline total loss is

$$
\mathcal L_{\mathrm{inverse}}
=\mathcal L_{\mathrm{physics}}+\mathcal L_{\mathrm{obs}}.
$$

The scales make the components dimensionless and keep their numerical
magnitudes comparable. They are numerical choices rather than additional
physical laws.

### 11.6 Joint optimization

Adam updates two parameter groups:

- neural-network weights at learning rate $10^{-3}$; and
- the raw conductance parameter at learning rate $5\times10^{-3}$.

At every epoch:

1. Predict temperatures at dense collocation times.
2. Calculate both ODE residuals using the current learned $K$.
3. Predict temperatures at the 13 observation times.
4. Calculate physics and observation losses.
5. Backpropagate through the network, derivatives, and $K$.
6. Update the network weights and raw conductance.
7. Record total loss, component losses, and physical $K$.

### 11.7 Default inverse configuration

| Setting | Default |
| --- | ---: |
| Initial $K$ | 0.2 W/K |
| True synthetic $K$ | 0.5 W/K |
| Observation interval | 5 s |
| Observation pairs | 13 |
| Hidden layers | 2 |
| Hidden width | 32 |
| Collocation points | 128 |
| Epochs | 4,000 |
| Network learning rate | $10^{-3}$ |
| Parameter learning rate | $5\times10^{-3}$ |
| Residual scale | 0.1 K/s |
| Observation scale | 1 K |
| Random seed | 7 |
| Device | CPU |

### 11.8 Current inverse result

The default noise-free CPU baseline gives approximately:

| Metric | Value |
| --- | ---: |
| True $K$ | 0.500000 W/K |
| Inferred $K$ | 0.499999 W/K |
| Cold dense-trajectory RMSE | 0.001922 K |
| Hot dense-trajectory RMSE | 0.001048 K |
| Cold observation RMSE | 0.001807 K |
| Hot observation RMSE | 0.000979 K |

This is successful recovery in a controlled synthetic problem. It is not yet
an uncertainty estimate or evidence of recovery from real sensor data.

### 11.9 Identifiability limiting case

Suppose $I=0$, both nodes remain at 300 K, and $T_h-T_c=0$ for all time. Then

$$
K(T_h-T_c)=0
$$

for every possible $K$. The temperatures and residuals contain no information
about the conductance. The gradient of the physics loss with respect to $K$ is
zero in this limiting case.

The test suite checks this explicitly. A positive parameter constraint can
prevent an unphysical negative estimate, but it cannot create information that
is absent from the experiment.

### 11.10 Conventional cold contact-resistance inference

The second inverse baseline uses the conventional four-node RK4 model rather
than a neural network. It infers one positive cold contact resistance from
ideal transient observations while holding every other parameter fixed.

The implementation lives in
[`contact_resistance_inference.py`](contact_resistance_inference.py). The
standalone walkthrough is
[`CONTACT_RESISTANCE_EXPERIMENT.md`](CONTACT_RESISTANCE_EXPERIMENT.md), and the
companion exercises are in
[`notes/14_contact_resistance_experiment.md`](notes/14_contact_resistance_experiment.md).

The cold contact connects $T_{cx}$ and $T_{cf}$:

$$
Q_{contact,c}=\frac{T_{cx}-T_{cf}}{R_{contact,c}}.
$$

The frozen hidden truth is 0.25 K/W. The other contact remains 0.25 K/W, the
module conductance remains 0.5 W/K, and all capacitances, reservoir couplings,
initial conditions, and external inputs remain at their contact-reference
values.

Three complete 60 s experiments are assigned by operating regime rather than
by random time point:

| Split | Current schedule | Purpose |
| --- | --- | --- |
| Train | 0 A to 5 s, +1 A to 20 s, then 0 A | Fit one resistance from turn-on and recovery |
| Validation | 0 A to 10 s, +0.6 A to 30 s, then 0 A | Check a new amplitude and timing |
| Test | 0, +1, 0, −1, 0 A at 5, 20, 35, and 50 s | Check an unseen bipolar regime |

Each regime uses a 0.1 s RK4 step and ideal observations every 1 s. All four
sensors are stored, giving 61 times and 244 records per regime. Only the cold
face and cold exchanger enter the equal-weight training loss:

$$
L(r)=\frac{1}{122}
\sum_{s\in\{cf,cx\}}\sum_{k=1}^{61}
\left[T_{s,k}^{pred}(r)-T_{s,k}^{obs}\right]^2.
$$

The hot-side sensor histories are evaluated only after fitting as coupled-model
consistency checks. Validation and test regimes are rejected if passed to the
fitting function.

The first sensitivity sweep produces:

| Candidate $R_{contact,c}$ | Training MSE |
| ---: | ---: |
| 0.10 K/W | 3.757467722442e-2 K² |
| 0.25 K/W | 0 K² |
| 0.50 K/W | 5.104280388841e-2 K² |

At training turn-off, 20 s, the cold face and exchanger are 297.448416 K and
298.990085 K. Their 1.541669 K separation is the maximum sampled contact gap.
At the same time, candidate gaps are 0.723369 K at 0.10 K/W and 2.279022 K at
0.50 K/W. This demonstrates useful sensitivity in the frozen problem.

Because only one scalar is unknown, a dependency-free golden-section search is
used instead of a neural network or multidimensional optimizer. The bounds are
0.05 to 1.0 K/W, the resistance-interval tolerance is 1e-8 K/W, and the maximum
is 96 iterations.

The frozen run takes 39 iterations and 42 loss evaluations. It obtains:

| Metric | Value |
| --- | ---: |
| True cold contact resistance | 0.250000000 K/W |
| Inferred cold contact resistance | 0.250000002 K/W |
| Relative parameter error | 6.078777e-7 % |
| Training fitted-pair RMSE | 1.698464e-9 K |
| Validation fitted-pair RMSE | 1.328620e-9 K |
| Test fitted-pair RMSE | 2.208849e-9 K |

Run the experiment with:

~~~bash
python3 -m thermotwin.contact_resistance_inference
~~~

The tiny errors arise because noise-free observations are generated and fit
with the same equations, fixed parameters, time step, and observation model.
This same-model synthetic baseline verifies code plumbing and establishes an
ideal one-parameter recovery limit. It does not establish hardware accuracy,
parameter uncertainty, multi-parameter identifiability, or robustness to
noise, bias, lag, missing records, and model discrepancy.

### 11.11 Repeated Gaussian-noise robustness study

The implemented follow-on experiment isolates random temperature noise while
preserving the same hidden physics, current regimes, observation times, and
one-parameter estimator. Its implementation is in
[`contact_resistance_noise_study.py`](contact_resistance_noise_study.py).

The frozen study makes these choices:

| Choice | Value |
| --- | ---: |
| Trials | 100 |
| Temperature-noise standard deviation | 0.05 K |
| First random seed | 2026 |
| Seeds consumed per trial | 3 |
| True cold contact resistance | 0.25 K/W |
| Search interval | 0.05--1.0 K/W |
| Search tolerance | 1e-6 K/W |

Each trial assigns a different seed to the train, validation, and test regime.
Trial $i$ uses seeds $2026+3i$, $2027+3i$, and $2028+3i$, respectively. Noise
is drawn independently for all four temperature sensors, but the estimator
still fits only the cold-face and cold-exchanger readings. The hot pair is not
allowed to influence the fitted parameter. Bias, lag, missingness, current
error, parameter error, and model discrepancy are disabled.

For each trial, the code regenerates the noisy observations, fits the cold
contact resistance to the noisy training regime, and evaluates the inferred
value on all three regimes. It records two deliberately different temperature
errors:

- observation RMSE compares predictions with the noisy readings actually
  available to the estimator; and
- truth RMSE compares the same predictions with the hidden ideal temperatures
  and is used only for synthetic evaluation.

Across trials, parameter bias is the signed mean of $r_i-r_{true}$, sample
standard deviation measures the spread of the estimates, and parameter RMSE
combines bias and spread through the root mean squared parameter error. The
5th and 95th percentiles are obtained by linear interpolation through the
ordered 100 estimates.

The frozen result is:

| Metric | Result |
| --- | ---: |
| Mean inferred resistance | 0.249782542 K/W |
| Sample standard deviation | 0.004116544 K/W |
| Mean parameter bias | -0.000217458 K/W |
| Parameter RMSE | 0.004101678 K/W |
| Empirical 5th percentile | 0.243722770 K/W |
| Empirical 95th percentile | 0.256246405 K/W |
| Search-bound hits | 0 |

The mean fitted-pair observation RMSEs are 0.049496, 0.050037, and
0.049789 K for train, validation, and test. Their proximity to 0.05 K checks
that the residual scale is consistent with the imposed measurement noise. The
corresponding hidden-truth RMSEs are 0.003580, 0.002800, and 0.004655 K. They
are much smaller because a fitted physical trajectory does not reproduce each
independent noise draw.

Run all 100 trials with:

~~~bash
python3 -m thermotwin.contact_resistance_noise_study
~~~

For a faster exploratory run, pass `--trials 5`. Reusing the frozen seeds
reproduces the same synthetic study; changing `--first-seed` draws another
empirical sample.

The mean estimate is close to the hidden truth, the parameter spread is about
1.65 percent of the true value, and no result reaches a search bound. Those
facts support robustness to this one isolated synthetic noise model. They do
not form a calibrated hardware uncertainty statement or a formal confidence
interval, and they say nothing yet about bias, lag, missing data, correlated
noise, uncertain physics, or several unknown parameters.

### 11.12 Fixed-bias contact-resistance study

The [contact_resistance_bias_study.py](contact_resistance_bias_study.py)
module asks how a constant calibration offset is misattributed when the
estimator still assumes ideal sensors. For sensor $s$,

$$
T_s^{observed}(t)=T_s^{ideal}(t)+b_s.
$$

Unlike zero-mean independent noise, $b_s$ persists at every time and does not
shrink when more readings or trials are averaged. Five deterministic cases
separate zero bias, individual offsets, common-mode error, and differential
contact-gap error:

| Bias case | Inferred resistance | Signed error |
| --- | ---: | ---: |
| Zero bias | 0.249999776 K/W | -0.000000224 K/W |
| Cold face +0.10 K | 0.208885282 K/W | -0.041114718 K/W |
| Cold exchanger +0.10 K | 0.272817055 K/W | +0.022817055 K/W |
| Both cold sensors +0.10 K | 0.228450366 K/W | -0.021549634 K/W |
| Face +0.05 K, exchanger -0.05 K | 0.218889695 K/W | -0.031110305 K/W |

Face and exchanger offsets move the fitted parameter in different directions
because they alter different parts of the coupled transient. Equal bias on
both sensors preserves their instantaneous temperature difference, but it does
not preserve their absolute histories relative to the reservoirs and the rest
of the model. Consequently, common-mode bias does not cancel from this loss.

Run the cases with:

~~~bash
python3 -m thermotwin.contact_resistance_bias_study
~~~

### 11.13 Sensor lag and contact-dynamics confusion

The [contact_resistance_lag_study.py](contact_resistance_lag_study.py) module
filters dense 0.1 s truth before sampling the result every 1 s. For one time
step, the exact first-order update is

$$
T_{s,k}^{lag}=a_k T_{s,k-1}^{lag}+(1-a_k)T_{s,k}^{ideal},
$$

$$
a_k=\exp\left(-\frac{\Delta t_k}{\tau_s}\right).
$$

Applying lag before output downsampling is important: the sensor state evolves
between reported readings. The estimator does not include $	au_s$ and is
allowed to change only contact resistance, so it tries to explain a sensor
dynamic as a physical contact dynamic.

| Lag case | Inferred resistance | Test observation RMSE |
| --- | ---: | ---: |
| Zero lag | 0.249999776 K/W | approximately 0 K |
| Cold face, 2 s | 0.246880379 K/W | 0.194466 K |
| Cold exchanger, 2 s | 0.270766427 K/W | 0.077482 K |
| Both cold sensors, 2 s | 0.270846727 K/W | 0.210732 K |
| Face 2 s, exchanger 0.5 s | 0.252142030 K/W | 0.195915 K |

The parameter shifts demonstrate confounding. The remaining held-out
residuals demonstrate that one static resistance cannot fully reproduce a
first-order sensor state. If capacitances were also trainable, lag could be
confused with them as well because both alter transient time response. This
study does not yet fit capacitance and therefore does not quantify that
multi-parameter ambiguity.

~~~bash
python3 -m thermotwin.contact_resistance_lag_study
~~~

### 11.14 Missing readings around informative turn-off

The
[contact_resistance_missingness_study.py](contact_resistance_missingness_study.py)
module removes both cold-sensor readings around every nonzero-to-zero current
transition. The relevant times are derived from each regime rather than using
one absolute outage window: 20 s for training, 30 s for validation, and 20 and
50 s for the bipolar test.

Noise-free remaining readings can still recover the exact same-model
parameter, so parameter error alone would incorrectly suggest that the missing
records have no consequence. The study therefore evaluates local curvature of
the unnormalized training sum of squared errors $J$:

$$
H_J\approx
\frac{J(r_0-\delta)-2J(r_0)+J(r_0+\delta)}{\delta^2},
$$

with $r_0=0.25$ K/W and $\delta=0.01$ K/W. Larger curvature means the loss
rises more sharply near the truth and provides a stronger local distinction
between nearby resistance values. It is a deterministic sensitivity proxy,
not a complete confidence interval or Fisher-information calculation.

| Training availability | Fitted records | SSE curvature |
| --- | ---: | ---: |
| Complete cold pair | 122 | 304.8575 |
| Remove 0--4 s equilibrium control | 112 | 304.8575 |
| Remove turn-off instant | 120 | 286.4841 |
| Remove plus-or-minus 2 s | 112 | 216.4959 |
| Remove plus-or-minus 5 s | 100 | 133.4655 |

Removing ten equilibrium readings has essentially no effect, while removing
the same number around turn-off reduces curvature by about 29 percent. The
wide turn-off outage removes fewer than one fifth of fitted records but more
than half of the local curvature.

~~~bash
python3 -m thermotwin.contact_resistance_missingness_study
~~~

### 11.15 Restricted sensor sets

The [contact_resistance_sensor_study.py](contact_resistance_sensor_study.py)
module changes which sensor definitions and records physically exist in the
dataset. The selected names also define the fitting loss; unavailable sensors
cannot silently enter evaluation.

| Available sensors | Records | SSE curvature |
| --- | ---: | ---: |
| Cold face and exchanger | 122 | 304.8575 |
| Cold face only | 61 | 208.8583 |
| Cold exchanger only | 61 | 95.9992 |
| Hot face and exchanger only | 122 | 1.9426 |
| All four | 244 | 306.8001 |

Every case recovers 0.25 K/W from exact same-model data, including the weak
hot-only case. The curvature reveals the practical distinction that exact
recovery hides: the cold face carries more than twice the local information of
the cold exchanger, the hot pair has less than 1 percent of the cold pair's
curvature, and adding both hot sensors to the cold pair adds less than 1
percent.

~~~bash
python3 -m thermotwin.contact_resistance_sensor_study
~~~

### 11.16 Combined measurement imperfections

The
[contact_resistance_combined_study.py](contact_resistance_combined_study.py)
module composes the agreed mechanisms in this order:

~~~text
dense truth -> lag -> 1 s sampling -> bias -> noise
            -> turn-off missingness -> restrict sensors
~~~

The frozen case uses:

- a 2 s cold-face sensor time constant;
- +0.10 K cold-face bias;
- independent 0.05 K Gaussian noise;
- the same seeds as the noise-only study for a paired comparison;
- missing cold-pair readings plus or minus 2 s around each turn-off; and
- only the cold face and cold exchanger as available sensors.

Across 100 trials, the result is:

| Metric | Combined result |
| --- | ---: |
| Mean inferred resistance | 0.201589285 K/W |
| Sample standard deviation | 0.005680841 K/W |
| Mean parameter bias | -0.048410715 K/W |
| Parameter RMSE | 0.048739579 K/W |
| Empirical 5th percentile | 0.192003358 K/W |
| Empirical 95th percentile | 0.210809525 K/W |
| Search-bound hits | 0 |

The mean observation RMSEs are 0.145442, 0.117285, and 0.213847 K for train,
validation, and test. Mean hidden-truth RMSEs are 0.049159, 0.039371, and
0.065644 K. The systematic parameter bias is about 8.5 times the random sample
standard deviation. More repeated trials can estimate the spread more
precisely, but they cannot correct the bias produced by a misspecified sensor
model.

The exact limiting case sets noise, bias, and lag to zero, disables outages,
and retains the cold pair. It recovers 0.249999776 K/W with errors below
1e-6, so the combined pipeline reduces correctly to the ideal inference.

~~~bash
python3 -m thermotwin.contact_resistance_combined_study
~~~

Use `--trials 5` for a shorter exploratory run. As in the noise-only study,
the empirical percentile interval is not a hardware confidence interval.

### 11.17 Inverse cold-contact-resistance PINN

[`inverse_contact_resistance.py`](inverse_contact_resistance.py) reuses the
validated four-output contact network and makes one physical parameter
trainable:

$$
R_{cc}=\mathrm{softplus}(r_{\mathrm{raw}})>0.
$$

The temperature network still predicts
$T_{cf},T_{hf},T_{cx},T_{hx}$. The cold contact heat in both adjacent energy
balances now uses the learned value:

$$
\dot q_{cc}=\frac{T_{cx}-T_{cf}}{R_{cc}}.
$$

The hot contact resistance, module coefficients, four capacitances, reservoir
conductances, initial temperatures, reservoirs, and external heat inputs all
remain fixed. Positivity prevents an unphysical estimate but does not make the
resistance identifiable when $T_{cx}-T_{cf}$ remains zero.

#### 11.17.1 Frozen inverse problem

The first learned contact inverse problem deliberately remains smooth:

| Choice | Value |
| --- | ---: |
| Current | Constant 1 A |
| Duration | 60 s |
| Hidden cold contact resistance | 0.25 K/W |
| Initial resistance guess | 0.50 K/W |
| Observed sensors | Cold face and cold exchanger |
| Observation times | 0, 5, 10, ..., 60 s |
| Paired observation times | 13 |
| Dense RK4 validation times | 601 |

Only the 26 cold-pair temperature values enter the observation loss. The hot
face and hot exchanger remain coupled through the physics, but their synthetic
temperatures are not labels. Dense RK4 histories are withheld until
post-training validation.

The constant-current choice isolates parameter learning from the derivative
discontinuities created by rectangular current switches. The previously
designed pulse regimes are retained as parameter-transfer tests, described
below.

#### 11.17.2 Physics and observation loss

The forward contact residual function accepts an optional differentiable cold
contact resistance. Ordinary forward training omits the override and keeps the
experiment value. Inverse training supplies the positive learned tensor, so
gradients pass from both cold contact balances into $r_{\mathrm{raw}}$.

The four normalized physics terms are

$$
\mathcal L_{\mathrm{physics}}
=\sum_{j\in\{cf,hf,cx,hx\}}
\mathrm{mean}\left[
\left(\frac{r_j}{0.1\ \mathrm{K/s}}\right)^2
\right].
$$

The cold-pair observation term is

$$
\mathcal L_{\mathrm{obs}}
=\mathrm{mean}\left[
\left(
\frac{T_{s,k}^{\mathrm{PINN}}-T_{s,k}^{\mathrm{obs}}}
{1\ \mathrm{K}}
\right)^2
\right],
\qquad s\in\{cf,cx\}.
$$

The baseline total is

$$
\mathcal L
=\mathcal L_{\mathrm{physics}}+\mathcal L_{\mathrm{obs}}.
$$

Both components are dimensionless after scaling. The 0.1 K/s and 1 K scales
are numerical conditioning choices, not new physical constants or measurement
uncertainties.

Adam updates the temperature-network parameters at $10^{-3}$ and the raw
resistance at $5\times10^{-3}$. The default uses 128 collocation points, two
hidden layers of 32 tanh units, 8,000 epochs, seed 13, and CPU.

#### 11.17.3 Conventional comparison and transfer

The dependency-free golden-section fitter receives the same sparse ideal
constant-current dataset and estimates the same single parameter. This is a
comparison of optimization representations:

- conventional search repeatedly integrates RK4 for candidate resistance
  values and minimizes temperature mismatch; and
- the inverse PINN jointly learns one continuous four-temperature trajectory
  and the resistance from physics plus sparse observations.

After fitting, the PINN resistance is inserted into the conventional RK4 model
for the established lower-amplitude validation pulse and bipolar test pulse.
This checks whether the learned physical parameter transfers to unseen control
regimes. It does **not** transfer or evaluate the constant-current neural
temperature function under those pulses.

#### 11.17.4 Frozen result

Run the complete comparison with:

~~~bash
python3 -m thermotwin.inverse_contact_resistance_report
~~~

The default CPU result is:

| Metric | Value |
| --- | ---: |
| True cold contact resistance | 0.250000000 K/W |
| Initial PINN resistance | 0.500000000 K/W |
| Inverse-PINN resistance | 0.250140756 K/W |
| Conventional resistance, same observations | 0.250000002 K/W |
| PINN absolute parameter error | 0.000140756 K/W |
| PINN relative parameter error | 0.056303 percent |
| Final normalized physics loss | $1.113218\times10^{-4}$ |
| Final normalized observation loss | $1.388674\times10^{-6}$ |

Dense constant-current temperature errors are:

| State | RMSE |
| --- | ---: |
| Cold face | 0.001542 K |
| Hot face | 0.000832 K |
| Cold exchanger | 0.000885 K |
| Hot exchanger | 0.001420 K |

The cold-face and cold-exchanger RMSE values at the 13 observed times are
0.001460 K and 0.000805 K. On unseen controls, conventional simulations using
the PINN parameter give all-sensor RMSE values of 0.000087 K for the
lower-amplitude validation pulse and 0.000145 K for the bipolar test pulse.

[`inverse_contact_resistance_report.py`](inverse_contact_resistance_report.py)
plots face and exchanger trajectories with observed points, all four dense
errors, total/physics/observation losses, resistance convergence against truth
and the conventional fit, and the cold contact temperature drop. The default
ignored output is
`thermotwin/figures/inverse_contact_resistance_comparison.png`.

The result is a same-model, ideal-sensor, one-unknown synthetic baseline. It
does not show recovery from the noise, bias, lag, missingness, restricted
sensor sets, simultaneous unknown parameters, model mismatch, or hardware
data already studied with the conventional estimator. The next section adds
switched-current inverse training while preserving this smooth reference.

Exercises are in
[`notes/16_inverse_contact_resistance_pinn.md`](notes/16_inverse_contact_resistance_pinn.md).

### 11.18 Piecewise inverse cold-contact-resistance PINN

[`piecewise_inverse_contact_resistance.py`](piecewise_inverse_contact_resistance.py)
combines the two separately validated capabilities:

1. the piecewise forward model represents known current switches with exact
   temperature continuity and independent one-sided rates; and
2. the smooth inverse model represents one positive trainable cold contact
   resistance and a joint physics-plus-observation loss.

Only the cold contact resistance is newly unknown. The pulse schedule, hot
contact resistance, thermoelectric coefficients, capacitances, reservoir
conductances, reservoir temperatures, initial state, and external heat inputs
remain fixed at their synthetic truth.

#### 11.18.1 Frozen pulse inference problem

The training experiment is the same whole unipolar regime used by the
conventional estimator and piecewise forward PINN:

~~~text
0 <= t < 5 s:    I = 0 A
5 <= t < 20 s:   I = 1 A
20 <= t <= 60 s: I = 0 A
~~~

The ideal virtual test stand samples all four sensors every 1 s, but only the
cold-face and cold-exchanger readings enter neural training. This produces 61
paired times and 122 observed temperatures. The current stored with records at
5 s is 1 A and at 20 s is 0 A, matching the right-continuous control
convention. Temperature observations themselves are continuous at those
instants.

| Choice | Value |
| --- | ---: |
| Current | 0--1--0 A pulse |
| Switches | 5 s and 20 s |
| Duration | 60 s |
| Hidden cold contact resistance | 0.25 K/W |
| Initial resistance guess | 0.50 K/W |
| Observed sensors | Cold face and cold exchanger |
| Observation interval | 1 s |
| Paired observation times | 61 |
| Observed temperatures | 122 |
| Dense RK4 validation times | 601 |

The dense four-state RK4 trajectory and all hot-side temperatures are withheld
from optimization. They are used only after training to evaluate the learned
trajectory. The conventional estimator receives the identical long-form
pulse dataset, not a separately generated approximation.

#### 11.18.2 One parameter shared across all segments

The model contains three independent four-output temperature subnetworks, but
only one raw resistance parameter. It is transformed as

$$
R_{cc}=\mathrm{softplus}(r_{raw})>0.
$$

That single value is used in the cold contact heat rate at every collocation
time:

$$
\dot q_{cc}(t)=\frac{T_{cx}(t)-T_{cf}(t)}{R_{cc}}.
$$

Giving each time segment its own resistance would describe a physically
changing contact and would let the model hide trajectory error in artificial
parameter jumps. Sharing one value expresses the current assumption that the
contact is constant throughout the experiment.

The first segment starts at the exact specified four-temperature state. Each
later segment starts at the previous segment's predicted endpoint. Consequently,

$$
\mathbf T_1(5^-)=\mathbf T_2(5^+),
\qquad
\mathbf T_2(20^-)=\mathbf T_3(20^+)
$$

by construction for every resistance and every set of network weights. The
temperature derivatives may still jump because the current and subnetworks
change at the boundaries.

#### 11.18.3 Joint normalized loss

The physics term is the same normalized four-residual sum used by the smooth
inverse PINN:

$$
\mathcal L_{physics}
=\sum_{j\in\{cf,hf,cx,hx\}}
\mathrm{mean}\left[
\left(\frac{r_j}{0.1\ \mathrm{K/s}}\right)^2
\right].
$$

The observation term uses the 122 cold-pair values:

$$
\mathcal L_{obs}
=\mathrm{mean}\left[
\left(
\frac{T_{s,k}^{PINN}-T_{s,k}^{obs}}{1\ \mathrm{K}}
\right)^2
\right],
\qquad s\in\{cf,cx\}.
$$

The frozen total loss is

$$
\mathcal L=\mathcal L_{physics}+20\mathcal L_{obs}.
$$

The factor 20 prevents the flexible temperature subnetworks from reducing the
physics loss while retaining a noticeably biased resistance and small but
systematic observation error. It is a numerical conditioning choice. It does
not create new measurements, change the physical energy balances, or mean the
sensors are twenty times more trustworthy. A low total loss remains
insufficient evidence of parameter accuracy, so the implementation reports the
resistance explicitly and compares it with hidden truth and conventional
search.

Collocation points are duration-weighted interval midpoints. They exclude 5 s
and 20 s because a two-sided classical temperature derivative is not defined
at an ideal current switch. Observation times may include the switches because
temperature is continuous and therefore has one unambiguous value there.

#### 11.18.4 Optimization and limiting case

Adam uses separate parameter groups:

| Setting | Default |
| --- | ---: |
| Hidden layers per segment | 2 |
| Hidden width | 32 |
| Temperature segments | 3 |
| Total collocation points | 192 |
| Epochs | 8,000 |
| Network learning rate | $10^{-3}$ |
| Resistance learning rate | $5\times10^{-3}$ |
| Physics weight | 1 |
| Observation weight | 20 |
| Residual scale | 0.1 K/s |
| Observation scale | 1 K |
| Temperature output scale | 10 K |
| Random seed | 19 |
| Device | CPU |

The resistance is not automatically identifiable merely because it is
positive. If current is zero, every node remains at the same equilibrium
temperature, and $T_{cx}-T_{cf}=0$, then $\dot q_{cc}=0$ for every positive
$R_{cc}$. Both the loss and its gradient with respect to the raw resistance
are then zero. This limiting case is tested directly.

#### 11.18.5 Conventional comparison and frozen result

Run the complete workflow with:

~~~bash
python3 -m thermotwin.piecewise_inverse_contact_resistance_report
~~~

The frozen CPU result is:

| Metric | Value |
| --- | ---: |
| True cold contact resistance | 0.250000000 K/W |
| Initial PINN resistance | 0.500000000 K/W |
| Piecewise inverse-PINN resistance | 0.250518948 K/W |
| Conventional resistance, same pulse observations | 0.250000002 K/W |
| PINN absolute parameter error | 0.000518948 K/W |
| PINN relative parameter error | 0.207579 percent |
| Final normalized physics loss | $7.443536\times10^{-4}$ |
| Final normalized observation loss | $2.049499\times10^{-5}$ |
| Maximum constructed boundary-temperature jump | 0 K |

Dense neural trajectory errors on the training pulse are:

| State | RMSE |
| --- | ---: |
| Cold face | 0.006704 K |
| Hot face | 0.002868 K |
| Cold exchanger | 0.001797 K |
| Hot exchanger | 0.002624 K |

The cold-face and cold-exchanger RMSE values at the 61 observed times are
0.006705 K and 0.001795 K. The conventional search recovers the exact
same-model value more closely because it repeatedly solves the fixed RK4
equations and optimizes only one scalar; the PINN simultaneously approximates
four continuous functions and the parameter.

Substituting the PINN estimate into the conventional solver gives all-sensor
RMSE values of 0.000322 K for the lower-amplitude validation pulse and
0.000534 K for the bipolar test pulse. These transfer checks validate the
physical parameter on unseen controls. They do not evaluate the three-segment
neural trajectory on a schedule with different transition times.

The eight-panel report includes face and exchanger trajectories, the current
schedule, all four dense errors, all four right-side physics residuals, loss
history, resistance convergence, and the cold contact temperature drop. Its
default ignored output is
`thermotwin/figures/piecewise_inverse_contact_resistance_comparison.png`.

#### 11.18.6 What this establishes and what comes next

This stage establishes that the neural inverse formulation can recover one
shared contact parameter while directly representing the informative current
switches. It remains an ideal, same-model, one-unknown result. The next
controlled comparisons should hold this implementation fixed while replacing
the ideal observations with, in order:

1. missing cold-pair readings around turn-off;
2. restricted sensor sets;
3. Gaussian temperature noise;
4. fixed sensor bias;
5. first-order sensor lag; and
6. the established combined-imperfection dataset.

Each case must be compared with the conventional estimator on identical
available records. The ideal result and the zero-imperfection limit should
remain regression tests. Multiple uncertain thermal parameters, model
mismatch, uncertainty intervals, and hardware validation remain later stages.

Exercises are in
[`notes/18_piecewise_inverse_contact_resistance.md`](notes/18_piecewise_inverse_contact_resistance.md).

---

## 12. What each test category checks

The tests live in `tests/` and use Python's `unittest` framework.

### 12.1 `test_thermoelectric.py`

Checks:

- nominal Peltier, Joule, conduction, heat-rate, and voltage values;
- $Q_h-Q_c=VI$ for positive, zero, and negative current;
- passive conduction at zero current;
- Peltier sign reversal and Joule invariance under current reversal;
- equal-temperature limiting cases;
- excessive-current reduction of $Q_c$; and
- COP behavior and its zero-power failure case.

### 12.2 `test_controls.py`

Checks:

- right-continuous step behavior;
- pulse return to baseline; and
- invalid schedule rejection.

### 12.3 `test_transient.py`

Checks:

- exact agreement with the two node balances;
- total stored-energy rate;
- equilibrium and passive-conduction signs;
- positive-current cooling/heating directions;
- capacitance scaling;
- invalid parameters and time settings;
- constant-rate and partial-step RK4 behavior;
- energy conservation for passive insulated nodes;
- steady-state algebraic consistency;
- long-time convergence toward steady state;
- scalar/scheduled constant-current equivalence; and
- exact pulse-boundary splitting.

### 12.4 `test_diagnostics.py`

Checks:

- initial hand calculations;
- energy identity at every sample;
- undefined COP at zero power;
- scheduled-current histories; and
- rejection of misaligned trajectory lengths.

### 12.5 `test_experiments.py`

Checks:

- the exact frozen reference inputs;
- initial hand calculations;
- 60 s RK4 regression values; and
- energy identity across the reference trajectory.

### 12.6 `test_forward_pinn.py`

Checks:

- exact initial-temperature enforcement;
- zero residual for the hand-calculated initial slopes;
- zero-current equilibrium residuals;
- rejection of switching current; and
- short CPU training and RK4 validation.

### 12.7 `test_forward_pinn_report.py`

Checks:

- alignment of all report histories;
- zero initial temperature error; and
- creation of a valid PNG report.

### 12.7a `test_contact_forward_pinn.py`

Checks:

- exact enforcement of all four initial temperatures;
- the hand-calculated startup slopes of -0.28, +0.16, 0, and 0 K/s;
- exact agreement of all four PINN residual equations with the conventional
  right-hand side at an arbitrary four-temperature state;
- the zero-current equal-temperature equilibrium limit;
- inclusion of all four mean-squared residual terms in the loss;
- rejection of switching current and invalid configurations;
- successful backpropagation through all four output derivatives; and
- short CPU training with all four RK4 RMSE values below 0.5 K.

### 12.7b `test_contact_forward_pinn_report.py`

Checks:

- use of the shared ignored `thermotwin/figures/` output location;
- alignment of reference, prediction, error, residual, and contact-drop
  histories;
- zero initial errors and contact drops for the frozen initial state; and
- creation of a valid six-panel PNG report.

### 12.7c `test_inverse_contact_resistance.py`

Checks:

- the exact 13-time ideal constant-current cold-pair dataset;
- positive resistance parameterization and all four exact initial states;
- the expected cold-face and cold-exchanger residual changes when contact
  resistance increases at a fixed temperature state;
- zero resistance gradient when no cold contact temperature drop develops;
- rejection of switching current in the first inverse-contact PINN;
- joint CPU training from a deliberately wrong 0.50 K/W initial guess;
- recovery of the 0.25 K/W hidden resistance;
- agreement with conventional scalar search on the same observations;
- transfer of the inferred parameter to unseen validation and test pulses; and
- rejection of malformed observations and optimization settings.

### 12.7d `test_inverse_contact_resistance_report.py`

Checks:

- use of the shared ignored figures directory;
- alignment of dense truth, learned trajectories, errors, observations,
  contact drops, losses, and parameter history;
- exact initial temperature errors; and
- creation of a valid inverse-comparison PNG.

### 12.7e `test_piecewise_contact_forward_pinn.py`

Checks:

- exact extraction of the three pulse intervals and their current values;
- the right-continuous current value and right-segment routing at switches;
- proportional midpoint collocation without transition points;
- exact four-temperature continuity while boundary rates remain free to jump;
- zero residual for analytically correct right-side startup slopes;
- the zero-current equilibrium limiting case;
- short CPU physics-only training with all four RK4 RMSE values below 0.1 K;
  and
- rejection of malformed schedules, current tensors, and configurations.

### 12.7f `test_piecewise_contact_forward_pinn_report.py`

Checks:

- use of the shared ignored figures directory;
- alignment of current, reference, prediction, error, residual, and loss
  histories;
- exact constructed continuity at both pulse transitions;
- agreement between plotted switch values and the right-continuous convention;
  and
- creation of a valid six-panel PNG report.

### 12.7g `test_piecewise_inverse_contact_resistance.py`

Checks:

- reuse of the established whole training pulse and 61-time ideal cold pair;
- right-continuous currents stored with observations at both switches;
- positive resistance parameterization and exact initial/interface states;
- exactly one resistance parameter shared by all three temperature segments;
- zero loss and zero resistance gradient in the no-contact-drop equilibrium
  limit;
- joint CPU training from the deliberately wrong 0.50 K/W initial value;
- recovery of the 0.25 K/W hidden resistance;
- agreement with conventional scalar search on identical pulse observations;
- transfer to the unseen lower-amplitude and bipolar regimes; and
- rejection of invalid observation times, collocation counts, and settings.

### 12.7h `test_piecewise_inverse_contact_resistance_report.py`

Checks:

- use of the shared ignored figures directory;
- alignment of current, dense truth, predictions, errors, residuals,
  observations, contact drops, losses, and resistance history;
- right-continuous switch values and exact constructed continuity;
- rejection of inconsistent training-history lengths; and
- creation of a valid eight-panel PNG report.

### 12.7i `test_pinn_showcase.py`

Checks:

- valid CPU-first epoch and device configuration;
- use of the shared ignored figures directory;
- exact alignment of forward and inverse time, current, and switch histories;
- preservation of exact constructed continuity in both workflows;
- inclusion of all 61 inverse observation times; and
- creation of a valid focused six-panel PNG.

### 12.8 `test_inverse_thermal_conductance.py`

Checks:

- 5 s sampling of the RK4 reference;
- positive $K$ and exact initial temperatures;
- expected residual changes when $K$ increases;
- non-identifiability when $T_h-T_c$ is always zero; and
- recovery of $K$ from sparse noise-free data.

### 12.9 `test_contact_transient.py`

Checks:

- contact heat signs and invalid resistance values;
- the complete four-rate hand calculation;
- whole-system energy closure;
- zero-current equilibrium and contact-only conservation;
- Peltier reversal under current reversal;
- RK4 final-step and current-transition handling;
- step-size refinement; and
- convergence toward the two-node aggregate as contact resistance decreases.

### 12.10 `test_contact_diagnostics.py`

Checks:

- initial contact and thermoelectric hand values;
- alignment of every derived history;
- module energy identity and whole-system energy closure;
- undefined module and delivered COP at zero power; and
- rejection of malformed trajectories.

### 12.11 `test_contact_experiments.py`

Checks:

- the exact frozen generic contact-reference inputs;
- initial predictions and 60 s regression values; and
- the transient distinction between module and delivered heat.

### 12.12 `test_contact_report.py`

Checks:

- report-history and sweep alignment;
- larger contact drops and lower cold delivered heat in the stated sweep;
- rejection of invalid sweep resistances; and
- creation of a valid PNG report.

### 12.13 `test_virtual_test_stand.py`

Checks:

- sensor-name, location, and sampling-interval validation;
- configurable and redundant sensor placement;
- exact start, regular, and final measurement times;
- linear interpolation and all four node-to-sensor mappings;
- right-continuous current alignment at a switch;
- the 61-time, 244-observation frozen reference schema;
- agreement of ideal final observations with hidden truth;
- filtering by sensor without exposing the dense trajectory;
- rejection of mislabeled, duplicate, unsorted, or malformed data; and
- explicit time, temperature, and current units.

### 12.14 `test_measurement_noise.py`

Checks:

- the frozen 0.05 K, seed-2026 generic configuration;
- rejection of negative, non-finite, duplicate, or malformed settings;
- zero noise as the exact ideal-data limiting case;
- identical readings for identical seeds and different readings for different
  seeds;
- preservation of time, current, sensor, location, unit, and count fields;
- both signs, near-zero sample mean, and expected RMS scale;
- named per-sensor standard-deviation overrides;
- stable random draws for unaffected sensors when one override changes;
- rejection of overrides for unknown sensors; and
- preservation of observation counts under the high-level noisy workflow and
  configurable downsampling.

### 12.15 `test_measurement_bias.py`

Checks:

- the frozen +0.10 K cold-face-only generic bias;
- rejection of non-finite, duplicate, or malformed bias settings;
- zero bias as the exact input-data limiting case;
- positive, negative, default, and named per-sensor offsets;
- preservation of time, current, sensor, location, unit, and count fields;
- persistence of the cold-face offset across all 61 measurements;
- rejection of overrides for unknown sensors;
- agreement of noise-then-bias and bias-then-noise to floating-point
  precision;
- retention of both configurations in the combined workflow; and
- configurable downsampling of the bias-only reference.

### 12.16 `test_measurement_lag.py`

Checks:

- the frozen 2 s cold-face-only generic time constant;
- rejection of negative, non-finite, duplicate, or malformed settings;
- zero lag as the exact input-data limiting case;
- equilibrium under constant temperature;
- the exponential response to a changed target;
- correct use of irregular observation intervals;
- rejection of overrides for unknown sensors;
- warmer cold-face readings during the cooling transient and no changes to
  other sensors;
- preservation of time, current, sensor, location, unit, and count fields;
- greater lag for a larger time constant;
- dense lag evaluation before output downsampling; and
- lag-before-bias/noise ordering with all configurations retained.

### 12.17 `test_measurement_missingness.py`

Checks:

- the frozen inclusive 20–30 s cold-face outage;
- rejection of empty names, invalid times, malformed configurations, and
  overlapping same-sensor intervals;
- support for simultaneous outages of different sensors;
- zero outages and out-of-experiment outages as exact no-effect limits;
- rejection of outages for unknown sensors;
- inclusive boundaries with floating-point tolerance;
- the expected 50 cold-face, 233 total, and 61 unique-time counts;
- exact preservation of other sensor histories, retained records, metadata,
  units, and the immutable input;
- support for complete loss of one sensor while other sensors remain;
- rejection of a configuration that removes every dataset record;
- correct behavior at another output sampling interval;
- lag-state continuation through the unavailable interval;
- exact lag-before-bias-before-noise-before-missingness composition;
- retention of all four measurement-model configurations; and
- the effect of applying seeded noise in the wrong order.

### 12.18 `test_contact_resistance_inference.py`

Checks:

- exact train, validation, and test current regimes;
- valid regime names, split labels, and piecewise-constant controls;
- replacement of only the candidate cold contact and current schedule;
- positive finite candidate resistance;
- complete ideal datasets with 61 times and 244 records per regime;
- nonempty, correctly labeled, uniquely named whole-regime splits;
- hidden-truth exclusion from inference datasets;
- right-continuous current with continuous switch temperatures;
- the frozen maximum 1.541669 K cold contact gap at 20 s;
- increasing driven contact gap with increasing resistance;
- an exact same-model training-loss minimum at 0.25 K/W;
- exclusion of hot-side readings from the fitting loss;
- valid scalar-search bounds and stopping values;
- rejection of validation regimes by the fitter;
- recovery of the hidden resistance with bounded search history; and
- low errors on the complete unseen validation and test regimes.

### 12.19 `test_contact_resistance_noise_study.py`

Checks:

- the frozen noise level, trial count, first seed, and search settings;
- rejection of invalid configurations and seed inputs;
- unique deterministic train, validation, and test seeds for every trial;
- zero noise as the exact ideal-dataset limiting case;
- same-seed reproducibility and changed-seed variation;
- preservation of regime, sensor, time, location, current, and count fields;
- recovery of the noise-free parameter limit;
- a frozen first noisy trial and reproducible five-trial run;
- direct agreement of reported bias and RMSE with trial values;
- ordered interpolated percentiles and zero one-trial sample deviation;
- absence of search-bound hits in the frozen small study; and
- inclusion of both observation and hidden-truth metrics in the text report.

### 12.20 `test_contact_resistance_robustness.py`

Checks:

- regular downsampling with sensor and unit preservation;
- immutable whole-regime transformation;
- ideal truth matched only to an incomplete dataset's available keys;
- one-sensor fitting and selected-sensor validation;
- rejection of empty, unknown, and unavailable fitting sensors;
- prediction pairing only at retained observation times;
- available-record counting and positive local SSE curvature; and
- rejection of a lag integration interval coarser than output sampling.

### 12.21 `test_contact_resistance_bias_study.py`

Checks:

- the five frozen zero, individual, common, and differential bias cases;
- exact recovery in the zero-bias limit;
- opposite parameter-shift directions for face and exchanger bias;
- frozen inferred values for all four nonzero cases;
- non-cancellation of common-mode bias in an absolute-temperature loss;
- persistent truth error on unseen regimes; and
- complete case and error-view reporting.

### 12.22 `test_contact_resistance_lag_study.py`

Checks:

- five frozen zero, individual, common, and asymmetric lag cases;
- dense-before-sparse zero lag as the exact ideal limit;
- different parameter effects from face and exchanger lag;
- frozen inferred values for all four nonzero cases;
- residual dynamic error that a resistance shift cannot remove;
- transfer of truth error to unseen regimes; and
- complete lag-case reporting.

### 12.23 `test_contact_resistance_missingness_study.py`

Checks:

- complete, equilibrium-control, instant, narrow, and wide outage cases;
- alignment to each regime's actual nonzero-to-zero transitions;
- unchanged information after removing equilibrium records;
- information loss after removing only the turn-off instants;
- monotonic record and curvature loss with wider turn-off windows;
- exact recovery from the remaining noise-free same-model data;
- loss of more than half the local curvature in the wide case; and
- reporting of record counts, curvature, and both error views.

### 12.24 `test_contact_resistance_sensor_study.py`

Checks:

- five frozen available-sensor sets;
- physical removal of unselected definitions and records;
- invalid, duplicate, and unknown sensor selections;
- record counts proportional to available sensors;
- exact same-model recovery from each set;
- the cold face's greater sensitivity than the cold exchanger;
- very weak hot-pair sensitivity to the cold contact; and
- additive curvature when cold and hot pairs are combined.

### 12.25 `test_contact_resistance_combined_study.py`

Checks:

- all frozen noise, bias, lag, outage, sensor, seed, and search choices;
- malformed combined configurations;
- the complete zero-imperfection limiting case;
- a frozen first combined trial;
- same-seed reproducibility and changed-seed variation;
- direct agreement of parameter RMSE with individual trials;
- systematic error larger than random trial spread; and
- explicit pipeline, control, observation-error, and truth-error reporting.

### 12.26 Operating-map, pulse-overlay, and PWM tests

The new operating tests check:

- all four algebraic contact-state balances and independent RK4 convergence;
- independence of steady temperature from thermal capacitance;
- cooling/heating energy closure and
  $\mathrm{COP}_h=\mathrm{COP}_c+1$ where both are meaningful;
- complete lift/current/contact grids and exclusion of tiny-capacity COP
  optima;
- equal-load contact penalties, extra face lift, and infeasible targets;
- agreement of warmed continuous transients with the exact steady envelope;
- rectangular-pulse mean and RMS current statistics;
- the frozen negative pulse result under both equal-cooling and equal-power
  comparisons;
- averaged thermoelectric energy closure using mean and mean-square current;
- direct-PWM duty-one and smoothed-PWM zero-ripple limiting cases;
- the separate effect of converter loss on wall COP; and
- valid PNG generation in the ignored package figures directory.

---

## 13. Validation levels and what they mean

ThermoTwin currently uses several different kinds of validation. They should
not be conflated.

### 13.1 Algebra and unit checks

These verify that equations, signs, identities, and dimensions are internally
consistent.

### 13.2 Limiting-case checks

These verify known behavior such as passive conduction, equilibrium, zero
current, insulated energy conservation, or absent identifiability.

### 13.3 Numerical solver cross-checks

RK4 step refinement, contact-model reduction toward the two-node aggregate,
and algebraic steady-state comparisons test the numerical implementation of
the conventional equations.

### 13.4 Forward PINN versus RK4

The two-node comparison verifies two temperature functions and two residuals.
The smooth contact-aware comparison separately verifies four temperature
functions, four residuals, and two derived interface drops. The piecewise
contact comparison additionally verifies known switched current, exact state
continuity, and independent one-sided rates. These checks establish that each
PINN approximates its corresponding conventional mathematical model. None
validates that mathematical model against hardware.

### 13.5 Synthetic inverse recovery

This verifies that the chosen network and loss can recover one parameter when
the data are generated from exactly the same equations. This is an important
baseline, but it is an easier problem than real inference with noise and model
mismatch.

### 13.6 Ideal observation-layer validation

The ideal test-stand tests verify that defined sensors sample the intended
synthetic states at the intended times and that hidden dense truth is not part
of the returned dataset. This validates data plumbing and schema semantics. It
does not establish realistic sensor behavior or agreement with hardware.

### 13.7 Synthetic measurement-noise validation

The noise tests verify deterministic random generation, schema preservation,
the zero-noise limit, and broad statistical properties of one controlled
sample. They do not establish the distribution, magnitude, independence, or
stationarity of errors from a real sensor.

### 13.8 Synthetic fixed-bias validation

The bias tests verify constant additive offsets, sensor isolation, schema
preservation, the zero-bias limit, and composition with Gaussian noise. They
do not establish that a real sensor has a constant offset or determine its
calibration bias from data.

### 13.9 Synthetic sensor-lag validation

The lag tests verify the first-order recurrence, zero-lag and equilibrium
limits, response direction, time-interval handling, dense-before-sparse
ordering, and composition with other synthetic effects. They do not identify
a real sensor time constant or validate the assumption that the sensor has no
thermal influence on the measured node.

### 13.10 Synthetic missing-observation validation

The missingness tests verify inclusive deterministic outages, exact retained
records, schema preservation, limiting cases, reference counts, and complete
pipeline ordering. They do not establish why real records go missing, whether
availability depends on an unobserved temperature, or whether the frozen
outage resembles hardware communication failures.

### 13.11 Synthetic contact-resistance inference validation

The contact-inference tests verify pulse-regime generation, whole-experiment
splitting, contact-gap sensitivity, bounded scalar optimization, exact ideal
recovery, and transfer to two unseen current schedules. They do not validate
the four-node model against hardware or quantify robustness when other
parameters and sensor properties are uncertain.

### 13.12 Synthetic Gaussian-noise parameter-robustness validation

The repeated-noise tests verify unique seed assignment, exact reproducibility,
the zero-noise inference limit, parameter summary calculations, and separate
evaluation against noisy observations and hidden truth. The frozen 100-trial
run measures empirical robustness when independent 0.05 K Gaussian errors are
the only imperfection. It does not validate the assumed noise distribution or
level, provide formal coverage guarantees, or include hardware and model
mismatch.

### 13.13 Synthetic fixed-bias parameter robustness

The bias-inference tests verify zero-bias reduction, deterministic sensor
isolation, directional parameter shifts, and transfer to unseen current
regimes. They show how an unmodeled constant offset is misattributed in this
one-parameter problem. They do not estimate a physical calibration offset or
show that a real bias remains constant.

### 13.14 Synthetic lag and contact-dynamics robustness

The lag-inference tests verify dense sensor-state evolution before sparse
sampling, the zero-lag limit, frozen parameter shifts, and held-out dynamic
residuals. They demonstrate contact-resistance confounding when sensor lag is
omitted. They do not infer sensor time constants, capacitances, or their joint
identifiability.

### 13.15 Synthetic informative-missingness validation

The turn-off tests verify regime-aligned outages, exact visible-record
matching, remaining-data recovery, and local SSE-curvature loss. They compare
missing equilibrium and switch-adjacent readings rather than treating all
records as equally informative. The curvature is a local deterministic
sensitivity measure, not a complete uncertainty calculation.

### 13.16 Synthetic restricted-sensor validation

The sensor-set tests verify that unavailable sensor definitions and records
are removed, only selected sensors enter the loss, and exact limiting-case
recovery is separated from practical sensitivity. They do not include sensor
cost, placement error, thermal loading, or hardware accessibility.

### 13.17 Synthetic combined-imperfection validation

The combined tests verify transformation order, exact zero-imperfection
reduction, seed reproducibility, empirical summaries, and a frozen trial. The
100-trial result demonstrates that systematic error can dominate random
spread. It does not establish how these imperfections interact in hardware,
validate their chosen magnitudes, or correct the misspecified measurement
model.

### 13.18 Synthetic inverse-contact PINN validation

The inverse-contact tests verify positive parameterization, local sensitivity,
an exact no-contact-drop identifiability limit, sparse-observation recovery,
agreement with scalar search, dense same-regime temperature errors, and
parameter transfer to two pulse regimes. They do not show that the neural
temperature function handles current switches or that the estimator is robust
to imperfect measurements, uncertain physics, multiple parameters, or real
hardware.

### 13.19 Synthetic switched-current contact-PINN validation

The piecewise-contact tests verify schedule segmentation, exact temperature
continuity, independent one-sided derivatives, right-continuous current,
transition-free collocation, limiting cases, physics-only convergence, and
agreement with a transition-splitting RK4 reference. They do not infer an
unknown parameter, prove that instantaneous current switching is physically
realistic, or validate the four-node equations against hardware.

### 13.20 Synthetic switched-current inverse-contact PINN validation

The piecewise inverse tests verify one positive resistance shared across all
segments, exact switch continuity, pulse-observation recovery, agreement with
conventional search on identical records, dense withheld-state errors, and
parameter transfer to two unseen schedules. The no-contact-drop test verifies
an exact non-identifiability limit. These checks do not establish robustness to
imperfect sensors, simultaneous unknowns, model mismatch, or hardware.

### 13.21 Hardware validation

Hardware validation will require measured temperatures, currents, voltages,
sensor timing and locations, calibration information, contact modeling, and a
careful comparison between predicted and observed behavior. That stage has not
yet been implemented.

---

## 14. Current physical and numerical assumptions

The current results depend on these assumptions:

1. $\alpha$, $R$, and $K$ are constant with temperature and current.
2. The thermoelectric module uses quasi-steady face heat-rate relations.
3. The two-node model uses two uniform temperatures; the contact-aware model
   uses four uniform face and exchanger temperatures.
4. Thermal energy is stored only in the selected lumped nodes, with no
   internal spatial temperature field inside the module.
5. Joule heat divides equally between the two faces.
6. Thomson heating is neglected.
7. Radiation is not modeled explicitly.
8. Reservoir temperatures remain constant during one run.
9. External heat inputs remain constant during one run.
10. The conventional current input is scalar or piecewise constant.
11. The original two-node forward PINN, smooth four-node contact forward PINN,
    inverse-$K$ PINN, and inverse-contact PINN use constant current only. The
    piecewise contact forward and inverse PINNs accept known
    piecewise-constant current.
12. Each current PINN inverse problem has one unknown parameter and noise-free
    paired temperature observations.
13. The virtual test-stand baseline uses exact, instantaneous temperature
    sensors at all four modeled nodes and records current without error.
14. The first noisy dataset adds independent Gaussian temperature errors with
    no bias, lag, missingness, temporal correlation, or current error.
15. The first bias-only dataset adds a constant +0.10 K cold-face offset. The
    combined workflow adds that bias and the frozen Gaussian noise model.
16. The first lag model uses a 2 s cold-face sensor time constant, initializes
    the sensor at the first node temperature, and does not feed back into the
    thermal state equations.
17. The first missingness model omits cold-face records from 20 through 30 s,
    inclusively, after noise generation. It represents failed reporting while
    the sensor and thermal model continue evolving.
18. The first contact-resistance inference uses ideal complete observations,
    treats only the cold contact resistance as unknown, fits the cold face and
    exchanger, and keeps entire current regimes in separate data splits.
19. The first inference-robustness study applies independent 0.05 K Gaussian
    errors to all four temperature sensors over 100 trials, gives each regime
    a unique seed, fits only the cold pair, and keeps every other measurement
    imperfection and source of model mismatch disabled.
20. The bias-inference study keeps bias constant throughout each experiment
    and varies only the two cold-sensor offsets.
21. The lag-inference study uses first-order output filters evaluated on 0.1 s
    synthetic truth before 1 s sampling, with no thermal feedback from the
    sensor state.
22. The turn-off missingness study removes both cold sensors around every
    nonzero-to-zero transition and uses local training-SSE curvature at the
    known synthetic truth as an information proxy.
23. The restricted-sensor study treats the selected sensor set as the complete
    available measurement schema and keeps all physical parameters exact.
24. The combined study uses cold-face lag and bias, independent Gaussian
    noise, regime-aligned cold-pair outages, and cold-pair-only availability;
    every other physical parameter remains known and exact.
25. The contact-aware forward PINN uses the same fixed four-node parameters as
    the conventional contact reference, gives all four residuals equal weight,
    and does not use temperature observations during training.
26. The inverse-contact PINN trains on 13 ideal cold-pair observation times
    under constant 1 A current, keeps every parameter except the cold contact
    resistance fixed, and uses the conventional solver—not its learned
    temperature network—for transfer checks on pulse regimes.
27. The piecewise contact forward PINN assigns a separate smooth subnetwork to
    each positive-duration constant-current interval, chains all four endpoint
    temperatures exactly, treats current as right-continuous, and keeps both
    contact resistances and every other physical parameter fixed.
28. The piecewise inverse contact PINN uses 61 ideal cold-pair times from the
    0--1--0 A training pulse, shares one positive cold contact resistance
    across three temperature subnetworks, weights the normalized observation
    loss by 20, and keeps every other physical parameter fixed.
29. The COP map assumes constant inputs, fixed reservoirs symmetric around
    300 K, 0--1.5 A current, zero external heat inputs, and a 1 W minimum useful
    rate when naming a maximum-COP point.
30. The first power-electronics layer prescribes direct-PWM peak current or
    smoothed triangular current ripple, assumes 95% converter efficiency and
    0.05 W fixed switching loss, and averages electrical current moments rather
    than resolving a converter circuit or switching edges.

### 14.1 Contact-resistance scope

The conventional four-node model, both contact-aware forward PINNs, and both
inverse contact PINNs include separate cold and hot thermal contact
resistances between TE faces and heat exchangers. The two-node solver,
two-node forward PINN, and inverse-$K$ PINN still omit those explicit
interfaces.

- $K$ is internal parasitic thermal conductance through the module.
- $R_{\mathrm{contact},c}$ and $R_{\mathrm{contact},h}$ are interface thermal
  resistances in K/W.
- $G_c$ and $G_h$ connect exchanger nodes to fixed reservoirs.
- $R$ remains module electrical resistance.

The conventional cold contact baseline infers one resistance from ideal
same-model synthetic data. The two inverse contact PINNs infer that cold
resistance from ideal constant-current and switched-current datasets,
respectively, while both contact forward PINNs keep both contacts fixed. None
of these workflows
calibrates a contact against hardware, and the hot contact has not been
inferred. The observation schema identifies modeled sensor locations and now
supports controlled noise, bias, lag, and missingness. Those effects remain
synthetic rather than empirically calibrated. The model does not yet represent
physical sensor geometry, random or value-dependent outages, sensor thermal
loading, electrical contact resistance, or flowing-fluid states. Neither
thermal contact resistance has yet been inferred from hardware data.

### 14.2 Engineering decision workflow

The engineering showcase connects four previously separate ideas into a
single CPU-first chain:

```text
accessible exchanger measurements
    -> hidden-loss and sensor inference
    -> local parameter uncertainty
    -> fair control comparison
    -> constrained next experiment
    -> standardized assembly fingerprint
```

Run the chain and save its evidence figure with:

```bash
python3 -m thermotwin.engineering_showcase
```

#### 14.2.1 Accessible-sensor inverse problem

The visible dataset contains only cold- and hot-exchanger temperatures. The
two thermoelectric-face temperatures are withheld. The current schedule has a
1 A pulse, a recovery interval, and a separate 0.55 A pulse. Both sensors have
a hidden 1.5 s first-order lag, independent biases, and 0.02 K Gaussian noise.
The cold sensor loses seven records around the first turn-off.

The estimator searches jointly over cold contact resistance and shared sensor
lag. For each candidate pair, it profiles the two constant sensor biases using
their analytic least-squares means. The frozen estimate is 0.25000 K/W for a
0.25000 K/W truth and 1.5359 s for a 1.5000 s lag. Both biases are recovered
within about 0.002 K, and the observation RMSE is 0.02151 K.

Finite-difference sensitivities give a local covariance for resistance, lag,
and both biases. The resistance-lag correlation is -0.583, which quantifies
their transient confounding rather than assuming it away. All four hidden
truths fall inside the local 95% intervals. Transferring the estimates to a
withheld positive-and-negative current schedule gives 0.00181 K noiseless
accessible-sensor RMSE.

The complete derivation, dataset definition, results, and limitations are in
[`SPARSE_SENSOR_EXPERIMENT.md`](SPARSE_SENSOR_EXPERIMENT.md).

#### 14.2.2 Fair continuous-versus-pulsed comparison

Useful cooling is defined as the time-averaged heat extracted from the cold
reservoir, $G_c(T_{c,\infty}-T_{x,c})$. Electrical input is the time integral
of $VI$. Candidates warm for 360 s and are compared over a 120 s window. The
window-averaged change in all four stored thermal energies must be below
0.05 W, preventing a pulse from receiving COP credit for an unfinished
transient.

For each 2, 5, and 8 W target, the code first solves for an optimized
continuous current. It then sweeps four periods and three duty cycles, solving
for the pulse amplitude that produces the same delivered cooling. Current,
temperature, reachability, and storage constraints are applied before the best
pulse is selected.

The best pulse loses in the current model: its COP is 21.82%, 24.18%, and
27.64% below the optimized continuous case at 2, 5, and 8 W. The conclusion
also holds at equal electrical power: the pulses deliver 11.23%, 11.88%, and
12.76% less cooling. The matched-cooling COP conclusion remains within 0.04
percentage points over the contact-resistance uncertainty interval from the
sparse inference. This negative result is retained because the
constant-property lumped model contains quadratic Joule heating but no
validated flow, spatial, or multi-assembly mechanism that makes pulsing more
efficient.

See
[`CONTROL_COMPARISON_EXPERIMENT.md`](CONTROL_COMPARISON_EXPERIMENT.md) for the
equations, candidate grid, result table, and interpretation.

#### 14.2.3 Constrained experiment selection

The planner considers 25 single pulses built from five amplitudes and five
durations. It estimates the local Jacobian with respect to log cold contact
resistance, log cold-face capacitance, log sensor lag, and two nuisance biases.
The score is the expected reduction in three-physical-parameter covariance
volume after the nuisance parameters are included.

Candidates must use no more than 30 J and remain inside 285--315 K face limits.
Seventeen pass. The planner selects 0.8 A for 20 s, using 27.66 J and providing
7.198 nats of expected information. In 250 repeated linearized noise trials,
it reduces joint log-parameter RMSE by 82.2% relative to the smallest feasible
0.4 A, 5 s pulse while maintaining approximately nominal 95% coverage.

The ranking method and its local-linear limitations are in
[`NEXT_EXPERIMENT_WALKTHROUGH.md`](NEXT_EXPERIMENT_WALKTHROUGH.md).

#### 14.2.4 Assembly fingerprint

The selected 0.8 A, 20 s pulse becomes a standardized synthetic quality test.
Five assemblies with cold contact resistances from 0.15 to 0.50 K/W are
observed through the two exchanger sensors with 0.02 K noise. One-dimensional
fits recover all five hidden values within their local 95% intervals and
separate low-loss, reference-band, and elevated-loss groups.

The classification thresholds are illustrative software defaults, not
manufacturing limits. The complete synthetic batch is documented in
[`ASSEMBLY_FINGERPRINT_EXPERIMENT.md`](ASSEMBLY_FINGERPRINT_EXPERIMENT.md).

#### 14.2.5 Hardware boundary

[`hardware_data.py`](hardware_data.py) validates future CSV files containing
time, current, cold- and hot-exchanger temperatures, and optional voltage. It
preserves blank temperature cells as missing observations. The loader cannot
establish sensor placement, calibration, or safe operating limits.

No hardware run has been performed. The required safety decisions, data
contract, experiment sequence, and withheld-validation rule are defined in
[`HARDWARE_VALIDATION_PROTOCOL.md`](HARDWARE_VALIDATION_PROTOCOL.md).

### 14.3 Efficiency operating maps and electrical drive

The operating-map extension separates three questions that are often blurred
together: steady thermoelectric efficiency, seconds-scale thermal pulsing, and
high-frequency switch-mode electrical drive.

#### 14.3.1 Exact steady-state map

For constant current and constant properties, the two-node and four-node
zero-storage balances form small linear systems. The algebraic solvers compute
exact equilibria without integrating every operating point for many thermal
time constants. Their outputs are checked against the original right-hand
sides and long RK4 trajectories.

The frozen map sweeps external reservoir lift from 0 to 30 K, current from
0.05 to 1.50 A, symmetric contact resistance through 0.10, 0.25, and 0.50 K/W,
and the reduced topology with no explicit interfaces. It records external,
exchanger, and face lifts separately. Useful steady heat is measured at the
reservoir boundary:

$$
\dot Q_{c,\mathrm{del}}=G_c(T_{c,\infty}-T_{x,c}),
\qquad
\dot Q_{h,\mathrm{del}}=G_h(T_{x,h}-T_{h,\infty}).
$$

Cooling and heating COP divide those rates by module terminal power. At steady
state the module and delivered rates agree, and energy closure gives
$\mathrm{COP}_h=\mathrm{COP}_c+1$ whenever both ratios are meaningful. A
reported maximum COP must deliver at least 1 W so a near-zero-power,
near-zero-capacity ratio is not labeled a useful optimum.

For baseline 0.25 K/W contacts, maximum useful cooling COP declines from
23.423 at zero external lift to 1.835 at 10 K, 0.697 at 20 K, and 0.195 at
30 K. The maximizing current moves from 0.15 A to the 1.5 A bound as lift
increases. At equal 3 W cooling, explicit contacts lower COP by 35.14% at 0 K,
20.73% at 10 K, and 19.30% at 20 K relative to the reduced topology. The 3 W
target is infeasible at 30 K under the current limit.

Run the map and report with:

```bash
python3 -m thermotwin.cop_operating_map
python3 -m thermotwin.cop_operating_map_report
```

The complete definitions, settings, tables, and limitations are in
[`COP_OPERATING_MAP_EXPERIMENT.md`](COP_OPERATING_MAP_EXPERIMENT.md).

#### 14.3.2 Seconds-scale pulse overlay

The original fair pulse sweep is now plotted on the zero-external-lift steady
COP envelope. The 360 s warm-up continuous points agree with the exact steady
map within 0.04%. The optimized 10 s, 75% duty pulse winners remain below the
envelope: their COP is 21.82%, 24.18%, and 27.64% lower at matched 2, 5, and
8 W delivered cooling.

For a zero-to-peak rectangular pulse,

$$
I_{\mathrm{mean}}=D I_{\mathrm{peak}},
\qquad
I_{\mathrm{rms}}=\sqrt{D} I_{\mathrm{peak}}.
$$

Displaying both statistics makes the physical penalty visible: Peltier heat
is linear in current, while Joule heat follows RMS current squared. The
storage-drift check remains below 0.013 W, so an unfinished transient is not
being counted as cooling.

Run the connected study with:

```bash
python3 -m thermotwin.pulse_operating_map_report
```

See
[`PULSE_OPERATING_MAP_EXPERIMENT.md`](PULSE_OPERATING_MAP_EXPERIMENT.md).

#### 14.3.3 Averaged PWM and wall-plug power

High-frequency electrical PWM is not simulated by shortening the thermal RK4
step. Instead, the thermoelectric heat equations retain the waveform moments
they require:

$$
\overline Q_c
=\alpha T_c\overline I
-\frac{1}{2}R\overline{I^2}
-K(T_h-T_c),
$$

$$
\overline Q_h
=\alpha T_h\overline I
+\frac{1}{2}R\overline{I^2}
-K(T_h-T_c).
$$

Direct zero-to-peak PWM has
$\overline{I^2}/\overline I^2=1/D$. Smoothed current with triangular
peak-to-peak ripple fraction $r$ has multiplier $1+r^2/12$. Thus, at 0.60 A
mean with a fixed 1.50 A direct peak, direct PWM produces 2.5 times the DC
Joule heat. The frozen 10% smoothed-ripple case produces only 1.0008 times.

PWM-derived supply power is

$$
P_{\mathrm{supply}}
=P_{\mathrm{module}}/\eta+P_{\mathrm{fixed}},
$$

so the report retains module COP and wall-plug COP separately. At 10 K lift
and 0.60 A mean, ideal DC delivers 1.950 W at cooling COP 1.757; the smoothed
case delivers the same module cooling at wall COP 1.600; direct PWM delivers
1.459 W at wall COP 0.620.

This is an averaged interface for later converter detail, not a complete
power-electronics circuit. Efficiency, fixed loss, and ripple are prescribed;
switching frequency, inductance, voltage, dead time, thermal limits, and a
current-control loop remain future work.

Run:

```bash
python3 -m thermotwin.pwm_power_electronics_report
```

See
[`PWM_POWER_ELECTRONICS_EXPERIMENT.md`](PWM_POWER_ELECTRONICS_EXPERIMENT.md).

The three corresponding physics-and-code exercise sheets are
[`notes/19_cop_operating_map.md`](notes/19_cop_operating_map.md),
[`notes/20_pulse_operating_envelope.md`](notes/20_pulse_operating_envelope.md),
and [`notes/21_pwm_power_electronics.md`](notes/21_pwm_power_electronics.md).

---

## 15. Current package structure

```text
thermotwin/
├── __init__.py
├── thermoelectric.py
├── controls.py
├── transient.py
├── contact_transient.py
├── contact_diagnostics.py
├── contact_experiments.py
├── contact_report.py
├── control_comparison.py
├── cop_operating_map.py
├── cop_operating_map_report.py
├── pulse_operating_map.py
├── pulse_operating_map_report.py
├── pwm_power_electronics.py
├── pwm_power_electronics_report.py
├── sparse_sensor_inference.py
├── experiment_selection.py
├── assembly_fingerprint.py
├── hardware_data.py
├── small_matrix.py
├── figure_paths.py
├── figures/                 # generated and ignored by Git
├── diagnostics.py
├── experiments.py
├── forward_pinn.py
├── forward_pinn_report.py
├── contact_forward_pinn.py
├── contact_forward_pinn_report.py
├── piecewise_contact_forward_pinn.py
├── piecewise_contact_forward_pinn_report.py
├── piecewise_inverse_contact_resistance.py
├── piecewise_inverse_contact_resistance_report.py
├── pinn_showcase.py
├── engineering_showcase.py
├── inverse_thermal_conductance.py
├── inverse_contact_resistance.py
├── inverse_contact_resistance_report.py
├── contact_resistance_inference.py
├── virtual_test_stand.py
├── measurement_noise.py
├── measurement_bias.py
├── measurement_lag.py
├── measurement_missingness.py
├── contact_resistance_noise_study.py
├── contact_resistance_robustness.py
├── contact_resistance_bias_study.py
├── contact_resistance_lag_study.py
├── contact_resistance_missingness_study.py
├── contact_resistance_sensor_study.py
├── contact_resistance_combined_study.py
├── CONTACT_RESISTANCE_EXPERIMENT.md
├── PINN_SHOWCASE.md
├── SPARSE_SENSOR_EXPERIMENT.md
├── CONTROL_COMPARISON_EXPERIMENT.md
├── COP_OPERATING_MAP_EXPERIMENT.md
├── PULSE_OPERATING_MAP_EXPERIMENT.md
├── PWM_POWER_ELECTRONICS_EXPERIMENT.md
├── NEXT_EXPERIMENT_WALKTHROUGH.md
├── ASSEMBLY_FINGERPRINT_EXPERIMENT.md
├── HARDWARE_VALIDATION_PROTOCOL.md
├── requirements-pinn.txt
├── README.md
├── README_detailed.md
└── notes/

tests/
├── test_thermoelectric.py
├── test_controls.py
├── test_transient.py
├── test_contact_transient.py
├── test_contact_diagnostics.py
├── test_contact_experiments.py
├── test_contact_report.py
├── test_control_comparison.py
├── test_cop_operating_map.py
├── test_cop_operating_map_report.py
├── test_pulse_operating_map.py
├── test_pulse_operating_map_report.py
├── test_pwm_power_electronics.py
├── test_pwm_power_electronics_report.py
├── test_sparse_sensor_inference.py
├── test_experiment_selection.py
├── test_assembly_fingerprint.py
├── test_hardware_data.py
├── test_small_matrix.py
├── test_engineering_showcase.py
├── test_diagnostics.py
├── test_experiments.py
├── test_forward_pinn.py
├── test_forward_pinn_report.py
├── test_contact_forward_pinn.py
├── test_contact_forward_pinn_report.py
├── test_piecewise_contact_forward_pinn.py
├── test_piecewise_contact_forward_pinn_report.py
├── test_piecewise_inverse_contact_resistance.py
├── test_piecewise_inverse_contact_resistance_report.py
├── test_pinn_showcase.py
├── test_inverse_thermal_conductance.py
├── test_inverse_contact_resistance.py
├── test_inverse_contact_resistance_report.py
├── test_virtual_test_stand.py
├── test_measurement_noise.py
├── test_measurement_bias.py
├── test_measurement_lag.py
├── test_measurement_missingness.py
├── test_contact_resistance_inference.py
├── test_contact_resistance_noise_study.py
├── test_contact_resistance_robustness.py
├── test_contact_resistance_bias_study.py
├── test_contact_resistance_lag_study.py
├── test_contact_resistance_missingness_study.py
├── test_contact_resistance_sensor_study.py
└── test_contact_resistance_combined_study.py
```

The core public API is re-exported from `thermotwin/__init__.py`. Executable
inference modules are imported directly from their named modules so they can
run cleanly with `python3 -m`. Optional PyTorch modules also remain direct
imports so importing the core package does not require PyTorch.

---

## 16. Development sequence from here

The planned learning and implementation sequence is:

1. Keep both conventional topologies, reports, and the learned baseline
   reproducible.
2. Preserve the ideal virtual test-stand dataset as a reproducible baseline.
3. Preserve the configurable downsampling, Gaussian-noise, fixed-bias,
   first-order-lag, and deterministic-missingness baselines.
4. Preserve whole-regime splitting and the conventional one-contact recovery
   baseline.
5. Preserve the isolated noise, bias, lag, missingness, and restricted-sensor
   inference limits.
6. Preserve the combined-imperfections study and its exact zero-imperfection
   reduction.
7. Preserve the fixed-parameter four-node contact PINN and its independent RK4
   comparison.
8. Preserve the ideal constant-current inverse contact PINN, conventional
   comparison, and pulse-regime parameter-transfer checks.
9. Preserve the piecewise fixed-parameter contact PINN, exact switch
   continuity, and independent RK4 pulse comparison.
10. Preserve the ideal piecewise inverse contact PINN, conventional comparison
    on identical pulse observations, and unseen-regime parameter transfer.
11. Preserve the one-command showcase as the concise evidence-backed
    demonstration of the validated forward and inverse capabilities.
12. Compare piecewise PINN and conventional recovery on the same missing,
    restricted-sensor, noisy, biased, lagged, and combined pulse observations.
13. Preserve the exchanger-only joint resistance/lag/bias inference,
    correlations, intervals, and withheld-schedule validation.
14. Preserve the equal-capacity control comparison, storage-drift safeguard,
    negative pulse result, and uncertainty stress test.
15. Preserve the constrained experiment ranking, repeated-noise check, and
    standardized synthetic assembly fingerprint.
16. Preserve the steady cooling/heating operating map, equal-load contact
    comparison, pulse-envelope overlay, and averaged PWM current-moment tests.
17. Calibrate a converter loss/ripple model only after its electrical topology
    or measured efficiency map is defined.
18. Extend the local experiment-selection validation to complete nonlinear
    repeated fits and additional uncertain physical parameters.
19. Compare physics-informed and observation-only learning on identical
    imperfect accessible-sensor datasets.
20. Validate against hardware only after the documented measurement
    definitions, safety limits, sensor locations, and fluid interfaces are
    agreed.

Both READMEs should be updated as each milestone changes package behavior. The
concise README should remain quick to scan; this detailed README should explain
the physics, implementation, validation, limitations, and workflow thoroughly.
