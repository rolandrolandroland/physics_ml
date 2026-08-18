# Cold contact-resistance inference and noise study

## 1. Purpose

This document is a standalone walkthrough of ThermoTwin's first conventional
contact-parameter inference experiment. It explains the physical question,
frozen assumptions, current schedules, synthetic-data generation, regime-level
data split, loss function, scalar optimizer, validation procedure, numerical
results, interpretation, and limitations. It also documents the first
100-trial extension with controlled Gaussian temperature noise.

The experiment asks:

> Can ideal transient temperature observations recover one unknown cold-side
> thermal contact resistance when every other model quantity is known?

This is a controlled synthetic baseline. The same four-node mathematical
model generates and fits the observations. Success verifies the inference
workflow under ideal conditions; it does not validate the model against
hardware.

The implementation is in
[`contact_resistance_inference.py`](contact_resistance_inference.py). The
repeated-noise implementation is in
[`contact_resistance_noise_study.py`](contact_resistance_noise_study.py). The
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

The follow-on study adds independent 0.05 K Gaussian temperature noise and
repeats the fit for 100 saved trials:

| Quantity | Repeated-noise result |
| --- | ---: |
| Mean inferred resistance | 0.249782542 K/W |
| Sample standard deviation | 0.004116544 K/W |
| Mean parameter bias | -0.000217458 K/W |
| Parameter RMSE | 0.004101678 K/W |
| Empirical 5th--95th percentiles | 0.243722770--0.256246405 K/W |
| Search-bound hits | 0 |

This second result measures empirical variation under one isolated synthetic
noise model. It is not a hardware uncertainty interval. Section 19 derives
the statistics, traces the code, and explains the limits of the conclusion.

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

## 15. Running the experiments

### 15.1 Ideal inference baseline

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

### 15.2 Repeated-noise study

Run the frozen 100-trial study with:

~~~bash
python3 -m thermotwin.contact_resistance_noise_study
~~~

Use a smaller trial count while exploring:

~~~bash
python3 -m thermotwin.contact_resistance_noise_study --trials 5
~~~

The command also accepts `--first-seed` and
`--noise-standard-deviation`. Changing either produces a different controlled
study, so report both values whenever results are compared.

Run the focused robustness tests with:

~~~bash
python3 -m unittest tests.test_contact_resistance_noise_study
~~~

---

## 16. What the ideal-inference tests protect

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
7. Under the isolated 0.05 K Gaussian-noise model, the 100-trial estimates
   remain centered near the hidden truth with a 0.00412 K/W sample standard
   deviation and no search-bound hits.

---

## 18. What has not been learned

This experiment does not establish:

- the cold contact resistance of physical hardware;
- the correctness of the four-node lumped model;
- the accuracy of any fixed thermal parameter;
- robustness to fixed bias, sensor lag, missing readings, correlated noise, or
  a noise level other than the one frozen synthetic case;
- identifiability when multiple parameters vary together;
- formal uncertainty bounds on the inferred resistance;
- correctness under temperature-dependent material properties;
- equivalence between contact paste, clamping pressure, geometry, and one
  constant lumped resistance; or
- safety of any current schedule on a real device.

The tiny reported errors should never be presented as physical measurement
accuracy.

---

## 19. Repeated Gaussian-noise robustness study

### 19.1 Question

The first robustness extension asks:

> If independent zero-mean temperature errors with a 0.05 K standard
> deviation are added, how much does the inferred cold contact resistance vary
> across repeated synthetic experiments?

One noisy fit is not enough to answer that question. It can land unusually
close to or far from the truth by chance. The implementation therefore runs
100 reproducible trials and summarizes the distribution of fitted parameters.

### 19.2 What is held fixed

This stage changes only the temperature observations. It preserves:

- the 0.25 K/W hidden cold contact resistance;
- all other physical parameters;
- the three complete train, validation, and test current regimes;
- the 0.1 s RK4 step and 1 s observation interval;
- all four sensor locations;
- the cold-face and cold-exchanger fitting pair; and
- the equal-weight least-squares loss.

Bias, lag, missing readings, current error, correlated noise, parameter error,
and model discrepancy remain disabled. That isolation is essential: if the
fit changes, this experiment lets us attribute the change to the imposed
random temperature error rather than to several mechanisms at once.

### 19.3 Frozen trial design and seed mapping

All four temperature sensors receive independent Gaussian errors with mean
zero and standard deviation 0.05 K. Trial $i$, counted from zero, uses:

$$
s_{train}=2026+3i,
$$

$$
s_{validation}=2027+3i,
$$

$$
s_{test}=2028+3i.
$$

Consequently, no regime or trial reuses a random seed. The seed mapping makes
the complete study reproducible while preserving distinct noise draws for all
three regimes.

### 19.4 One-trial data path

Each trial follows this sequence:

~~~text
ideal four-node RK4 datasets
        |
        +--> independent noise on train, validation, and test observations
        |
        +--> fit R_contact,c using only the noisy cold training pair
        |
        +--> evaluate that same estimate on all three noisy regimes
        |
        +--> compare again with hidden ideal temperatures for analysis only
~~~

The optimizer searches from 0.05 to 1.0 K/W. The noise study uses a 1e-6 K/W
interval tolerance and at most 64 golden-section iterations. This tolerance is
far smaller than the parameter variation caused by 0.05 K noise and reduces
unnecessary repeated simulation. The frozen fits require 32 loss evaluations
per trial.

### 19.5 Why two temperature RMSEs are reported

Observation RMSE compares a prediction with the noisy readings:

$$
RMSE_{obs}=\sqrt{\frac{1}{N}\sum_{j=1}^{N}
\left(T_j^{pred}-T_j^{noisy}\right)^2}.
$$

This is the error an estimator can calculate from the available dataset.

Truth RMSE compares the same prediction with the hidden ideal temperatures:

$$
RMSE_{truth}=\sqrt{\frac{1}{N}\sum_{j=1}^{N}
\left(T_j^{pred}-T_j^{ideal}\right)^2}.
$$

This second quantity is available only because the experiment is synthetic.
It measures trajectory error without asking the model to reproduce individual
random errors. A physical experiment would not reveal exact hidden truth.

### 19.6 Parameter statistics

For estimates $r_1,\ldots,r_n$ and true resistance $r_{true}$, the report uses:

$$
bias=\frac{1}{n}\sum_{i=1}^{n}(r_i-r_{true}),
$$

$$
RMSE_r=\sqrt{\frac{1}{n}\sum_{i=1}^{n}(r_i-r_{true})^2},
$$

and the sample standard deviation with denominator $n-1$. The empirical 5th
and 95th percentiles are linearly interpolated through the ordered estimates.
A bound-hit count checks whether the optimizer is being truncated by its
allowed interval.

### 19.7 Frozen 100-trial results

Run the study from the repository root:

~~~bash
python3 -m thermotwin.contact_resistance_noise_study
~~~

The saved configuration produces:

| Parameter metric | Result |
| --- | ---: |
| Trials | 100 |
| Mean inferred resistance | 0.249782542 K/W |
| Sample standard deviation | 0.004116544 K/W |
| Mean parameter bias | -0.000217458 K/W |
| Parameter RMSE | 0.004101678 K/W |
| Empirical 5th percentile | 0.243722770 K/W |
| Empirical 95th percentile | 0.256246405 K/W |
| Search-bound hits | 0 |

| Mean fitted-pair RMSE | Train | Validation | Test |
| --- | ---: | ---: | ---: |
| Against noisy observations | 0.049496 K | 0.050037 K | 0.049789 K |
| Against hidden ideal truth | 0.003580 K | 0.002800 K | 0.004655 K |

The mean estimate is 0.000217 K/W below the truth, while the trial-to-trial
standard deviation is 0.004117 K/W. Thus the observed bias is small compared
with the random spread in this finite study. The standard deviation is about
1.65 percent of the 0.25 K/W truth. No estimate reaches either search bound.

The observation errors remain close to the imposed 0.05 K scale. The smaller
truth errors show that the inferred physical trajectory remains much closer to
the ideal trajectory than to every individual noisy reading. The test truth
error is larger than the validation truth error because the bipolar test
schedule has a different sensitivity to a resistance error; this does not
mean its sensors received more noise.

### 19.8 Reproduction and exploration

A shorter development run is available without changing the frozen default:

~~~bash
python3 -m thermotwin.contact_resistance_noise_study --trials 5
~~~

`--first-seed` selects another reproducible set of trials, and
`--noise-standard-deviation` changes the isolated noise scale. The exact
zero-noise case is tested as the ideal-data limiting case.

The central objects are:

- `ContactResistanceNoiseStudyConfig`, which freezes the study controls;
- `ContactResistanceNoiseSeeds`, which records the three seeds in one trial;
- `run_contact_resistance_noise_trial`, which performs one fit and evaluation;
- `run_contact_resistance_noise_study`, which repeats and summarizes trials;
  and
- `ContactResistanceNoiseStudySummary`, which stores parameter and
  temperature-error statistics.

The focused tests are in `tests/test_contact_resistance_noise_study.py`. They
check validation, seed uniqueness, exact reproducibility, schema preservation,
the zero-noise limit, frozen regression values, statistic calculations, and
the generated report.

### 19.9 Correct interpretation and limitations

The 5th--95th percentile range is an empirical interval across these 100
saved synthetic trials. It is not automatically a 90 percent confidence
interval for hardware, a guarantee of repeated-sample coverage, or a Bayesian
credible interval. The result assumes that the model and every non-noise
quantity are exactly correct.

The study has learned that the current one-parameter estimator is not strongly
destabilized by independent 0.05 K Gaussian temperature errors in the frozen
same-model problem. It has not learned whether a physical sensor has that
error distribution, whether its errors are independent, or how inference
behaves when systematic and physical uncertainties interact.

---

## 20. Planned progression

The next controlled extensions are:

1. add fixed bias and study systematic parameter error;
2. add sensor lag and test confusion with thermal capacitance;
3. add the frozen missing-reading interval;
4. fit using restricted sensor sets;
5. combine imperfections only after their isolated effects are understood;
6. compare conventional least squares with an inverse PINN;
7. infer one contact resistance while perturbing other assumed-known values;
8. quantify profile likelihood, bootstrap uncertainty, and practical
   identifiability; and
9. use sensitivity to select the next most informative experiment.

Each extension should preserve the ideal result and zero-imperfection result
as limiting-case regression tests.
