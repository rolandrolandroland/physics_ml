# Cold contact-resistance inference experiment

## 1. Purpose

This document is a standalone walkthrough of ThermoTwin's first conventional
contact-parameter inference experiment. It explains the physical question,
frozen assumptions, current schedules, synthetic-data generation, regime-level
data split, loss function, scalar optimizer, validation procedure, numerical
results, interpretation, and limitations.

The experiment asks:

> Can ideal transient temperature observations recover one unknown cold-side
> thermal contact resistance when every other model quantity is known?

This is a controlled synthetic baseline. The same four-node mathematical
model generates and fits the observations. Success verifies the inference
workflow under ideal conditions; it does not validate the model against
hardware.

The implementation is in
[`contact_resistance_inference.py`](contact_resistance_inference.py). The
learning exercises are in
[`notes/14_contact_resistance_experiment.md`](notes/14_contact_resistance_experiment.md).

---

## 2. Result at a glance

The hidden synthetic cold contact resistance is 0.25 K/W. A bounded,
dependency-free golden-section search using only the unipolar training pulse
recovers:

| Quantity | Result |
| --- | ---: |
| True cold contact resistance | 0.250000000 K/W |
| Inferred cold contact resistance | 0.250000002 K/W |
| Absolute parameter error | approximately 1.52e-9 K/W |
| Relative parameter error | 6.078777e-7 % |
| Golden-section iterations | 39 |
| Loss evaluations | 42 |

The inferred resistance also reproduces two unseen current regimes:

| Split | Regime | Fitted cold-pair RMSE | All-sensor RMSE |
| --- | --- | ---: | ---: |
| Train | +1 A unipolar pulse | 1.698464e-9 K | 1.204815e-9 K |
| Validation | +0.6 A shifted pulse | 1.328620e-9 K | 9.420546e-10 K |
| Test | +1/−1 A bipolar pulse | 2.208849e-9 K | 1.563720e-9 K |

These errors are extremely small because the observations are noise-free and
the candidate simulator uses the same equations, numerical step, and fixed
parameters as the generator. This favorable situation is sometimes called an
inverse crime. It is useful as a software and identifiability baseline, but it
is much easier than real parameter inference.

---

## 3. Physical topology

The contact-aware model has four dynamic temperatures:

| Symbol | Node |
| --- | --- |
| $T_{cf}$ | Cold thermoelectric face |
| $T_{hf}$ | Hot thermoelectric face |
| $T_{cx}$ | Cold heat exchanger |
| $T_{hx}$ | Hot heat exchanger |

The cold contact resistance $R_{contact,c}$ connects the cold exchanger to the
cold module face. The hot contact resistance $R_{contact,h}$ connects the hot
module face to the hot exchanger.

The cold contact heat rate is positive from the cold exchanger toward the
cold face:

$$
Q_{contact,c}=\frac{T_{cx}-T_{cf}}{R_{contact,c}}.
$$

The hot contact heat rate is positive from the hot face toward the hot
exchanger:

$$
Q_{contact,h}=\frac{T_{hf}-T_{hx}}{R_{contact,h}}.
$$

The four transient energy balances are

$$
C_{cf}\frac{dT_{cf}}{dt}=Q_{contact,c}-Q_c,
$$

$$
C_{hf}\frac{dT_{hf}}{dt}=Q_h-Q_{contact,h},
$$

$$
C_{cx}\frac{dT_{cx}}{dt}
=G_c(T_{c,\infty}-T_{cx})+\dot q_{c,ext}-Q_{contact,c},
$$

$$
C_{hx}\frac{dT_{hx}}{dt}
=G_h(T_{h,\infty}-T_{hx})+\dot q_{h,ext}+Q_{contact,h}.
$$

The thermoelectric face heat rates remain

$$
Q_c=\alpha I T_{cf}-\frac{1}{2}I^2R-K(T_{hf}-T_{cf}),
$$

$$
Q_h=\alpha I T_{hf}+\frac{1}{2}I^2R-K(T_{hf}-T_{cf}).
$$

Only $R_{contact,c}$ is inferred. Every other quantity in these equations is
fixed.

---

## 4. Why a pulse is informative

A constant current eventually approaches a steady state. Steady data can
contain information about contact resistance, but it may be difficult to
separate that information from module conductance, reservoir coupling, or
other thermal resistances.

A pulse adds two transitions:

1. current turns on and changes Peltier and Joule heat rates; and
2. current turns off and removes those active terms.

Temperatures remain continuous at each switch because every node has finite
thermal capacitance. Temperature derivatives can change immediately. The face
and exchanger then respond on different time scales, creating a transient
temperature difference across the contact.

A larger cold contact resistance weakens face-to-exchanger coupling. During
the driven pulse it generally produces:

- a colder, more isolated cold face;
- a warmer, more slowly responding cold exchanger relative to the face; and
- a larger value of $T_{cx}-T_{cf}$.

The recovery after turn-off provides passive relaxation information in
addition to the powered response.

---

## 5. Frozen physical and numerical parameters

All three regimes use the same generic reference values:

| Quantity | Value |
| --- | ---: |
| Seebeck coefficient $\alpha$ | 0.05 V/K |
| Electrical resistance $R$ | 2.0 ohm |
| Module thermal conductance $K$ | 0.5 W/K |
| Cold-face capacitance | 50 J/K |
| Cold-exchanger capacitance | 50 J/K |
| Hot-face capacitance | 100 J/K |
| Hot-exchanger capacitance | 100 J/K |
| Hidden cold contact resistance | 0.25 K/W |
| Fixed hot contact resistance | 0.25 K/W |
| Cold reservoir conductance | 2.0 W/K |
| Hot reservoir conductance | 4.0 W/K |
| All initial node temperatures | 300 K |
| Both reservoir temperatures | 300 K |
| Both external heat inputs | 0 W |
| Experiment duration | 60 s |
| RK4 time step | 0.1 s |
| Observation interval | 1.0 s |

The values are generic learning parameters, not measurements of a particular
thermoelectric assembly.

---

## 6. Current regimes and split

Whole experiments are assigned to splits. Individual time points are never
randomly divided between training and evaluation.

### 6.1 Training regime

| Time interval | Current |
| --- | ---: |
| 0 to 5 s | 0 A |
| 5 to 20 s | +1 A |
| 20 to 60 s | 0 A |

This unipolar pulse is the only regime used to select the resistance.

### 6.2 Validation regime

| Time interval | Current |
| --- | ---: |
| 0 to 10 s | 0 A |
| 10 to 30 s | +0.6 A |
| 30 to 60 s | 0 A |

The different amplitude and switching times check whether the inferred
resistance transfers beyond the training waveform.

### 6.3 Test regime

| Time interval | Current |
| --- | ---: |
| 0 to 5 s | 0 A |
| 5 to 20 s | +1 A |
| 20 to 35 s | 0 A |
| 35 to 50 s | −1 A |
| 50 to 60 s | 0 A |

The bipolar test is the most different held-out schedule. Current reversal
changes the sign of the Peltier term while Joule heating remains positive.

### 6.4 Right-continuous switch convention

The current schedule is right-continuous. At exactly 5 s in the training
regime, the recorded current is +1 A. The node temperatures are still 300 K at
that instant because they cannot jump. At exactly 20 s, the recorded current
is 0 A while the temperatures retain the values reached immediately before
turn-off.

---

## 7. Synthetic observation generation

For each regime, ThermoTwin performs these steps:

1. construct a four-node experiment using the hidden 0.25 K/W resistance;
2. integrate all four temperatures with RK4 at 0.1 s;
3. stop integration steps exactly at current transitions;
4. sample one ideal sensor at each of the four nodes every 1 s;
5. attach the right-continuous current to every long-form observation; and
6. return 61 times and 244 records without returning the dense trajectory.

The three regime datasets contain the current schedules and observations.
They do not contain a `true_contact_resistance` or hidden trajectory field.
The true value is used later only to score the completed synthetic recovery.

No measurement imperfection is active:

- no random noise;
- no fixed bias;
- no sensor lag; and
- no missing readings.

This isolates parameter recovery from observation-model complications.

---

## 8. Sensors used for fitting and checking

All four sensor histories are stored:

- cold face;
- cold exchanger;
- hot face; and
- hot exchanger.

Only the cold face and cold exchanger enter the fitting objective. They are
the two temperatures directly separated by the unknown cold contact.

The hot-side temperatures are withheld from the objective. After fitting,
they provide an independent consistency check within each regime. They are
not independent hardware data because the same synthetic model generated
them, but they can expose an implementation that matches the cold pair while
disturbing the rest of the coupled model.

---

## 9. Training loss

For candidate resistance $r$, the simulator generates cold-face and
cold-exchanger predictions at every training observation time. With
$s\in\{cf,cx\}$ and $N=61$ times, the loss is

$$
L(r)=\frac{1}{2N}
\sum_{s\in\{cf,cx\}}\sum_{k=1}^{N}
\left[T_{s,k}^{pred}(r)-T_{s,k}^{obs}\right]^2.
$$

The loss has units K squared. Both sensors and every time receive equal
weight. The initial 0 A interval is included even though it has little or no
sensitivity to contact resistance at exact equilibrium.

The training function accepts only datasets labeled `train`. Passing a
validation or test regime to the fitter raises an error.

---

## 10. Sensitivity before optimization

The frozen experiment explicitly evaluates three candidate resistances before
interpreting the optimizer:

| Candidate resistance | Training MSE |
| ---: | ---: |
| 0.10 K/W | 3.757467722442e-2 K² |
| 0.25 K/W | 0 K² |
| 0.50 K/W | 5.104280388841e-2 K² |

The corresponding fitted-pair RMSE values for the incorrect candidates are
approximately 0.19384 K and 0.22593 K. The exact zero at 0.25 K/W occurs
because the same deterministic simulator generated the observations.

At the training pulse turn-off, 20 s, the cold contact gap changes strongly
with resistance:

| Resistance | Cold face | Cold exchanger | $T_{cx}-T_{cf}$ |
| ---: | ---: | ---: | ---: |
| 0.10 K/W | 297.902608 K | 298.625977 K | 0.723369 K |
| 0.25 K/W | 297.448416 K | 298.990085 K | 1.541669 K |
| 0.50 K/W | 297.046956 K | 299.325978 K | 2.279022 K |

These distinguishable histories establish sensitivity in this controlled
problem. Sensitivity alone does not prove practical identifiability when
other parameters or sensor errors are unknown.

---

## 11. Scalar optimizer

Only one positive scalar is unknown, so the first conventional estimator does
not require PyTorch, SciPy, gradients, or an initial guess. It uses a bounded
golden-section search.

| Search choice | Value |
| --- | ---: |
| Lower resistance bound | 0.05 K/W |
| Upper resistance bound | 1.0 K/W |
| Resistance-interval tolerance | 1e-8 K/W |
| Maximum iterations | 96 |

Golden-section search maintains an interval containing the best region found.
At each iteration it compares two interior candidates, discards the worse
side, and reuses one previous evaluation. The frozen run converges in 39
iterations and 42 loss evaluations.

The search bounds enforce positivity and cover the generic truth. A result at
a bound would be a warning that the range, data, model, or identifiability
needs review.

---

## 12. Training transient results

Selected ideal training observations are:

| Time | Current | Cold face | Cold exchanger | Cold contact gap |
| ---: | ---: | ---: | ---: | ---: |
| 0 s | 0 A | 300.000000 K | 300.000000 K | 0 K |
| 5 s | +1 A | 300.000000 K | 300.000000 K | 0 K |
| 6 s | +1 A | 299.732848 K | 299.989572 K | 0.256724 K |
| 10 s | +1 A | 298.865345 K | 299.800846 K | 0.935501 K |
| 15 s | +1 A | 298.067299 K | 299.411668 K | 1.344368 K |
| 20 s | 0 A | 297.448416 K | 298.990085 K | 1.541669 K |
| 21 s | 0 A | 297.604115 K | 298.918046 K | 1.313930 K |
| 30 s | 0 A | 298.430921 K | 298.818330 K | 0.387409 K |
| 60 s | 0 A | 299.367531 K | 299.448204 K | 0.080673 K |

The maximum sampled cold contact gap is 1.541669 K at 20 s. The cold face also
reaches its minimum sampled temperature, 297.448416 K, at 20 s. After current
turn-off, the face warms and the contact gap decays toward zero.

---

## 13. Inference and held-out results

The fitted parameter is

$$
R_{contact,c}^{fit}=0.250000002\ \mathrm{K/W}.
$$

Per-sensor RMSE values are:

| Regime | Cold face | Cold exchanger | Hot face | Hot exchanger |
| --- | ---: | ---: | ---: | ---: |
| Training | 1.988106e-9 K | 1.347960e-9 K | 1.790815e-10 K | 6.847273e-11 K |
| Validation | 1.566795e-9 K | 1.037119e-9 K | 1.312767e-10 K | 4.660876e-11 K |
| Test | 2.329057e-9 K | 2.081711e-9 K | 1.400523e-10 K | 5.695359e-11 K |

The unseen-regime results show that the recovered scalar transfers across the
two frozen schedules. They do not demonstrate broad machine-learning
generalization: the same known differential equations are evaluated with one
recovered parameter.

---

## 14. Code path

The main code objects are:

| Object | Responsibility |
| --- | --- |
| `ContactResistanceRegime` | Names one current schedule and whole-data split |
| `ContactResistanceRegimeDataset` | Pairs a regime with its ideal observations |
| `ContactResistanceDatasetSplit` | Keeps train, validation, and test experiments separate |
| `contact_resistance_experiment` | Inserts one candidate resistance into fixed physics |
| `simulate_contact_resistance_observations` | Runs RK4 and returns ideal observations |
| `contact_resistance_training_loss` | Computes cold-pair MSE for training regimes |
| `ContactResistanceSearchConfig` | Defines positive bounds and stopping settings |
| `fit_cold_contact_resistance` | Performs golden-section scalar minimization |
| `evaluate_contact_resistance_regime` | Calculates all sensor RMSE values |
| `run_contact_resistance_inference_experiment` | Runs the complete frozen workflow |
| `format_contact_resistance_inference_report` | Produces the command-line text report |

The high-level workflow is:

~~~text
freeze current regimes
    -> generate hidden truth separately for each regime
    -> sample ideal four-sensor observations
    -> keep whole regimes in train/validation/test
    -> simulate candidate resistance on training regime
    -> minimize cold-face/cold-exchanger MSE
    -> freeze inferred resistance
    -> evaluate validation and test regimes
    -> compare with hidden truth only after fitting
~~~

---

## 15. Running the experiment

From the repository root, run:

~~~bash
python3 -m thermotwin.contact_resistance_inference
~~~

Expected report:

~~~text
cold contact resistance inference
true resistance: 0.250000000 K/W
inferred resistance: 0.250000002 K/W
relative parameter error: 6.078777e-07 %
search evaluations: 42
train unipolar_training_pulse: fitted-pair RMSE=1.698464e-09 K, all-sensor RMSE=1.204815e-09 K
validation lower_amplitude_validation_pulse: fitted-pair RMSE=1.328620e-09 K, all-sensor RMSE=9.420546e-10 K
test bipolar_test_pulse: fitted-pair RMSE=2.208849e-09 K, all-sensor RMSE=1.563720e-09 K
~~~

Run the focused tests with:

~~~bash
python3 -m unittest tests.test_contact_resistance_inference
~~~

---

## 16. What the tests protect

The focused tests verify:

- exact train, validation, and test current schedules;
- whole-regime splitting and unique labels;
- positive candidate resistance and search bounds;
- preservation of all fixed physical parameters;
- ideal 61-time, 244-record datasets;
- hidden-truth exclusion from inference datasets;
- right-continuous current and continuous switch temperatures;
- the frozen 20 s contact-gap regression value;
- increasing driven contact gap with increasing resistance;
- an exact synthetic loss minimum at 0.25 K/W;
- exclusion of hot-side readings from the fitting loss;
- rejection of validation data by the fitter;
- scalar recovery and bounded search history;
- low error on unseen whole regimes; and
- reproducible report formatting.

---

## 17. What has been learned

Within the frozen mathematical model:

1. The unipolar pulse creates a clearly resistance-sensitive cold contact
   temperature gap.
2. Cold-face and cold-exchanger histories are sufficient to recover one
   resistance when every other quantity is known.
3. A dependency-free scalar optimizer is enough for this one-parameter
   baseline.
4. Whole-regime evaluation prevents adjacent-time leakage.
5. The recovered resistance reproduces unseen amplitudes, timings, and current
   reversal when the model is exact.
6. Hot-side histories provide a useful consistency check even though they do
   not enter the loss.

---

## 18. What has not been learned

This experiment does not establish:

- the cold contact resistance of physical hardware;
- the correctness of the four-node lumped model;
- the accuracy of any fixed thermal parameter;
- robustness to Gaussian noise, fixed bias, sensor lag, or missing readings;
- identifiability when multiple parameters vary together;
- uncertainty bounds on the inferred resistance;
- correctness under temperature-dependent material properties;
- equivalence between contact paste, clamping pressure, geometry, and one
  constant lumped resistance; or
- safety of any current schedule on a real device.

The tiny reported errors should never be presented as physical measurement
accuracy.

---

## 19. Planned progression

The controlled baseline supports the following staged extensions:

1. repeat the scalar fit with several search bounds and training schedules;
2. add Gaussian temperature noise over many saved seeds;
3. add fixed bias and study systematic parameter error;
4. add sensor lag and test confusion with thermal capacitance;
5. add the frozen missing-reading interval;
6. fit using restricted sensor sets;
7. compare conventional least squares with an inverse PINN;
8. infer one contact resistance while perturbing other assumed-known values;
9. quantify profile likelihood, bootstrap uncertainty, and practical
   identifiability; and
10. use sensitivity to select the next most informative experiment.

Each extension should preserve the ideal result as a limiting-case regression
test.
