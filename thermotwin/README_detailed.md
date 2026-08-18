# ThermoTwin: detailed physics and implementation guide

This document is the tutorial-style companion to the concise
[`README.md`](README.md). It explains what the package currently does, the
physical meaning of its equations, how the conventional and learned models are
connected, and how to run and validate each stage.

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
15. Conventional least-squares inference of one cold contact resistance.
16. A 100-trial Gaussian-noise robustness study of that inference.
17. Fixed-bias inference cases separating individual, common, and differential
    cold-sensor offsets.
18. Dense-before-sparse sensor-lag inference cases.
19. Regime-aligned turn-off missingness and a local information metric.
20. Cold-face, cold-exchanger, hot-pair, and all-sensor availability studies.
21. A 100-trial combined-imperfections inference study.
22. A forward physics-informed neural network, or PINN.
23. An RK4-versus-PINN comparison report.
24. A first inverse PINN that infers the module thermal conductance $K$ from
   sparse synthetic temperature observations.
25. Unit, sign, energy, sampling, measurement, numerical, PINN, and
    identifiability tests.

The package does **not** yet represent a hardware-validated digital twin. Its
learned models are currently validated against the conventional equations that
generated their synthetic reference data.

---

## 1. How to use this documentation

There are three documentation layers:

- [`README.md`](README.md) is the concise package reference.
- `README_detailed.md`, this file, is the step-by-step technical walkthrough.
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

The current suite contains 219 focused tests. Optional learned-model and report
tests are skipped
when their optional dependencies are not installed.

### 2.2 Install the optional learned-model dependencies

The forward and inverse PINNs require PyTorch. The contact and PINN reports
require Matplotlib:

```bash
python3 -m pip install -r thermotwin/requirements-pinn.txt
```

### 2.3 Run the main workflows

Train and validate the forward PINN:

```bash
python3 -m thermotwin.forward_pinn
```

Generate the four-panel forward comparison report:

```bash
python3 -m thermotwin.forward_pinn_report
```

Generate the contact-aware comparison and resistance sweep:

~~~bash
python3 -m thermotwin.contact_report
~~~

Run the first inverse problem and infer $K$:

```bash
python3 -m thermotwin.inverse_thermal_conductance
```

Both report commands write to `thermotwin/figures/` by default. The shared
location is defined in `figure_paths.py`, created automatically when needed,
and ignored by Git because generated PNG reports are outputs rather than source
code. Pass `--output PATH` to either command when a deliberate alternate
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

Future options include splitting the time domain at switches or explicitly
handling transition points in a time-dependent-control PINN.

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

This verifies that the PINN approximates the conventional mathematical model.
It does not validate the mathematical model against hardware.

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

### 13.18 Hardware validation

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
11. The first forward and inverse PINNs use constant current only.
12. The first inverse problem has one unknown parameter and noise-free paired
    temperature observations.
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

### 14.1 Contact-resistance scope

The conventional four-node model includes separate cold and hot thermal
contact resistances between TE faces and heat exchangers. The two-node solver,
forward PINN, and inverse-$K$ PINN still omit those explicit interfaces.

- $K$ is internal parasitic thermal conductance through the module.
- $R_{\mathrm{contact},c}$ and $R_{\mathrm{contact},h}$ are interface thermal
  resistances in K/W.
- $G_c$ and $G_h$ connect exchanger nodes to fixed reservoirs.
- $R$ remains module electrical resistance.

The conventional cold contact baseline infers one resistance from ideal
same-model synthetic data. It does not calibrate either contact against
hardware, and the hot contact has not been inferred. The observation schema
identifies modeled sensor locations, but it does not
yet represent physical sensor geometry, empirically calibrated noise, bias,
lag, or missingness, random or value-dependent outages, automated calibration,
sensor thermal loading, electrical contact resistance, or flowing-fluid
states. Neither thermal contact resistance has yet been inferred from hardware
data.

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
├── figure_paths.py
├── figures/                 # generated and ignored by Git
├── diagnostics.py
├── experiments.py
├── forward_pinn.py
├── forward_pinn_report.py
├── inverse_thermal_conductance.py
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
├── test_diagnostics.py
├── test_experiments.py
├── test_forward_pinn.py
├── test_forward_pinn_report.py
├── test_inverse_thermal_conductance.py
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
7. Compare inverse PINN recovery with conventional least squares on the same
   imperfect observations.
8. Extend practical-identifiability studies to uncertain physical parameters
   and simultaneous unknowns.
9. Extend the learned model to time-varying current.
10. Compare continuous and pulsed control strategies.
11. Rank candidate experiments by sensitivity or predicted information gain.
12. Validate against hardware only after measurement definitions, safety
    limits, sensor locations, and fluid interfaces are agreed.

Both READMEs should be updated as each milestone changes package behavior. The
concise README should remain quick to scan; this detailed README should explain
the physics, implementation, validation, limitations, and workflow thoroughly.
