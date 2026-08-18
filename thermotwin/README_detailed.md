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
12. A forward physics-informed neural network, or PINN.
13. An RK4-versus-PINN comparison report.
14. A first inverse PINN that infers the module thermal conductance $K$ from
   sparse synthetic temperature observations.
15. Unit, sign, energy, sampling, noise, numerical, PINN, and identifiability
    tests.

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

The current suite contains 110 focused tests. Optional learned-model and report
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

## 11. First inverse problem: learning $K$

The inverse implementation lives in
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

### 13.9 Hardware validation

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

### 14.1 Contact-resistance scope

The conventional four-node model includes separate cold and hot thermal
contact resistances between TE faces and heat exchangers. The two-node solver,
forward PINN, and inverse-$K$ PINN still omit those explicit interfaces.

- $K$ is internal parasitic thermal conductance through the module.
- $R_{\mathrm{contact},c}$ and $R_{\mathrm{contact},h}$ are interface thermal
  resistances in K/W.
- $G_c$ and $G_h$ connect exchanger nodes to fixed reservoirs.
- $R$ remains module electrical resistance.

The observation schema identifies modeled sensor locations, but it does not
yet represent physical sensor geometry, empirically calibrated noise or bias,
lag, missingness, automated calibration, electrical contact resistance, or
flowing-fluid states. Neither thermal contact resistance has yet been inferred
from data.

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
├── virtual_test_stand.py
├── measurement_noise.py
├── measurement_bias.py
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
└── test_measurement_bias.py
```

The core public API is re-exported from `thermotwin/__init__.py`. Optional
PyTorch modules are imported directly so importing the core package does not
require PyTorch.

---

## 16. Development sequence from here

The planned learning and implementation sequence is:

1. Keep both conventional topologies, reports, and the learned baseline
   reproducible.
2. Preserve the ideal virtual test-stand dataset as a reproducible baseline.
3. Preserve the configurable downsampling, Gaussian-noise, and fixed-bias
   baselines, then add lag and missing observations one mechanism at a time.
4. Split datasets by operating regime rather than by random time samples.
5. Infer one contact resistance while holding $K$ and the other interface
   parameters fixed.
6. Compare inverse PINN recovery with conventional least squares.
7. Quantify uncertainty and practical identifiability across repeated trials.
8. Extend the learned model to time-varying current.
9. Compare continuous and pulsed control strategies.
10. Rank candidate experiments by sensitivity or predicted information gain.
11. Validate against hardware only after measurement definitions, safety
    limits, sensor locations, and fluid interfaces are agreed.

Both READMEs should be updated as each milestone changes package behavior. The
concise README should remain quick to scan; this detailed README should explain
the physics, implementation, validation, limitations, and workflow thoroughly.
