# 14 — Cold contact-resistance inference experiment

Status: `Not started`

## Purpose

This worksheet develops both the physics and code understanding required for
ThermoTwin's first conventional contact-parameter inference experiment.

The experiment first uses ideal synthetic temperature observations to infer
one unknown cold thermal contact resistance. It then repeats the fit over 100
independently seeded 0.05 K Gaussian-noise trials. Every other physical
parameter is held fixed. One current-pulse regime is used for fitting, a
different pulse is used for validation, and a bipolar pulse is held out for
testing. Later blocks isolate fixed bias, sensor lag, informative missing
readings, and restricted sensors before tracing their combined effect.

Complete the prediction exercises before reading the result sections of
`thermotwin/CONTACT_RESISTANCE_EXPERIMENT.md` or running the high-level
experiment.

The relevant files are:

- `thermotwin/contact_transient.py`;
- `thermotwin/contact_experiments.py`;
- `thermotwin/controls.py`;
- `thermotwin/virtual_test_stand.py`;
- `thermotwin/contact_resistance_inference.py`;
- `thermotwin/contact_resistance_noise_study.py`;
- `thermotwin/contact_resistance_robustness.py`;
- `thermotwin/contact_resistance_bias_study.py`;
- `thermotwin/contact_resistance_lag_study.py`;
- `thermotwin/contact_resistance_missingness_study.py`;
- `thermotwin/contact_resistance_sensor_study.py`;
- `thermotwin/contact_resistance_combined_study.py`;
- `tests/test_contact_resistance_inference.py`;
- `tests/test_contact_resistance_noise_study.py`;
- `tests/test_contact_resistance_robustness.py`;
- the five corresponding bias, lag, missingness, sensor, and combined study
  test files; and
- `thermotwin/CONTACT_RESISTANCE_EXPERIMENT.md`.

---

## Frozen experiment decisions

| Choice | Frozen value |
| --- | --- |
| Inferred parameter | Cold contact resistance only |
| Hidden synthetic truth | 0.25 K/W |
| Other physical parameters | Fixed at contact-reference values |
| Initial and reservoir temperatures | 300 K |
| External heat inputs | 0 W |
| Duration | 60 s |
| RK4 step | 0.1 s |
| Observation interval | 1.0 s |
| Stored sensors | All four nodes |
| Sensors entering loss | Cold face and cold exchanger |
| Training regime | 0 A, +1 A pulse, 0 A recovery |
| Validation regime | Shifted +0.6 A pulse |
| Test regime | +1 A and −1 A bipolar pulse |
| Measurement imperfections | None |
| Estimator | Bounded golden-section least squares |
| Search bounds | 0.05 to 1.0 K/W |
| Noise robustness extension | 100 trials at 0.05 K standard deviation |
| First noise seed | 2026; three unique regime seeds per trial |
| Bias cases | Individual, common-mode, and differential cold offsets |
| Lag cases | Dense 0.1 s filtering before 1 s sampling |
| Missingness cases | Regime-aligned cold-pair turn-off windows |
| Sensor cases | Single cold, cold pair, hot pair, and all four |
| Combined case | Lag, bias, noise, missingness, and cold-pair restriction |

---

## Block 1 — Reconstruct the physical problem

### Exercise 1: Draw the four-node topology

Draw the thermal network containing:

- cold reservoir;
- cold exchanger;
- cold contact resistance;
- cold thermoelectric face;
- thermoelectric module;
- hot thermoelectric face;
- hot contact resistance;
- hot exchanger; and
- hot reservoir.

Label the four dynamic temperatures and indicate the positive direction of
both contact heat rates.

**My diagram:**

### Exercise 2: Write the contact heat laws

Starting from thermal resistance, write expressions for:

1. cold contact heat from exchanger to face; and
2. hot contact heat from face to exchanger.

State the units of temperature difference, resistance, and heat rate. Verify
that kelvin divided by K/W gives watts.

**My derivation:**

### Exercise 3: Complete the cold-side balances

Write the cold-face and cold-exchanger energy balances. Include:

- cold contact heat;
- module cold-side heat $Q_c$;
- reservoir coupling;
- external cold heat; and
- both thermal capacitances.

Explain the sign of every term.

**My balances:**

### Exercise 4: Complete the hot-side balances

Write the hot-face and hot-exchanger balances. Explain why positive hot
contact heat leaves the hot face but enters the hot exchanger.

**My balances:**

### Exercise 5: Identify what is known and unknown

Make two lists.

Known exactly in the first synthetic inverse problem:

- thermoelectric parameters;
- all four capacitances;
- reservoir conductances;
- hot contact resistance;
- current schedule;
- initial conditions; and
- external heat inputs.

Unknown:

- cold contact resistance.

Why would simultaneous uncertainty in capacitance or reservoir conductance
make this a harder inverse problem?

**My explanation:**

### Checkpoint 1

Ask Codex to review Exercises 1–5 before studying the current schedules.

---

## Block 2 — Understand the current regimes

### Exercise 6: Write the training schedule

The training current is:

| Time | Current |
| --- | ---: |
| 0–5 s | 0 A |
| 5–20 s | +1 A |
| 20–60 s | 0 A |

Write the corresponding `PiecewiseConstantCurrent` values and transition
times without looking at the implementation.

**My code prediction:**

### Exercise 7: Predict switch behavior

At exactly 5 s:

1. what current is recorded?
2. can any temperature jump?
3. which heat-rate terms change immediately?
4. which temperature derivatives may change?

Repeat at exactly 20 s.

**My prediction:**

### Exercise 8: Explain the baseline interval

Why include five seconds at 0 A before the pulse if the model begins at exact
equilibrium?

Discuss its usefulness for:

- confirming initial conditions;
- checking current alignment;
- revealing sensor bias in later extensions; and
- identifying contact resistance in the ideal baseline.

Which purpose provides little resistance information here?

**My explanation:**

### Exercise 9: Compare the three regimes

Explain what changes between:

1. the +1 A training pulse;
2. the shifted +0.6 A validation pulse; and
3. the +1/−1 A bipolar test pulse.

Why is a different current amplitude more informative for validation than a
copy of the training schedule?

**My comparison:**

### Exercise 10: Explain current reversal

When current changes from +1 A to −1 A:

1. what happens to the sign of the Peltier term?
2. what happens to $I^2R$ Joule heating?
3. why can this help separate thermoelectric and contact effects?
4. why is the bipolar regime kept out of the fitting loss?

**My explanation:**

### Checkpoint 2

Ask Codex to review Exercises 6–10 before predicting temperature responses.

---

## Block 3 — Predict the transient physics

### Exercise 11: Predict the first second after turn-on

At 5 s all four nodes are at 300 K. The current becomes +1 A.

Without running the solver, predict the signs of:

- $dT_{cf}/dt$;
- $dT_{hf}/dt$;
- $dT_{cx}/dt$; and
- $dT_{hx}/dt$

immediately after turn-on. Use the module face heat rates and zero initial
contact temperature drops to justify each sign.

**My prediction:**

### Exercise 12: Predict development of the cold contact gap

Define

$$
\Delta T_{contact,c}=T_{cx}-T_{cf}.
$$

1. What is it at 5 s?
2. Why should it become positive during cooling?
3. Which node initially changes faster?
4. Does a positive gap mean heat flows toward or away from the cold face?

**My explanation:**

### Exercise 13: Compare low and high contact resistance

For the same current pulse, predict how increasing cold contact resistance
from 0.10 to 0.50 K/W changes:

- cold-face temperature;
- cold-exchanger temperature;
- the contact temperature gap;
- contact heat transfer for a fixed gap; and
- face-to-exchanger equalization speed.

Be careful: the actual heat rate and gap both change dynamically, so do not
assume one remains fixed unless you state it explicitly.

**My prediction:**

### Exercise 14: Predict recovery after turn-off

At 20 s the current becomes zero.

1. Which Peltier and Joule terms disappear?
2. Which conductive and reservoir terms remain?
3. Should the cold face initially warm or cool?
4. Should the contact gap grow or shrink?
5. Why may the system still be away from 300 K at 60 s?

**My prediction:**

### Exercise 15: Estimate a contact time scale

Use the rough products $R_{contact,c}C_{cf}$ and
$R_{contact,c}C_{cx}$ with 0.25 K/W and 50 J/K.

1. Calculate both products in seconds.
2. Compare them with the 15 s powered interval.
3. Compare them with the 1 s observation interval.
4. Why is this only a rough guide for the coupled four-node system?

**My calculation:**

### Checkpoint 3

Ask Codex to review Exercises 11–15 before generating synthetic data.

---

## Block 4 — Understand the synthetic datasets

### Exercise 16: Separate hidden truth from observations

Describe the difference between:

1. the mathematical continuous-time temperature solution;
2. the 0.1 s RK4 trajectory;
3. the 1 s four-sensor observations; and
4. the dataset received by the scalar fitter.

Which object contains 601 times? Which contains 61 times and 244 long-form
records? Which must stay hidden from inference?

**My explanation:**

### Exercise 17: Calculate observation counts

For one 60 s experiment sampled every 1 s, calculate:

1. the number of measurement times;
2. the number of records for one sensor;
3. the number of records for four sensors; and
4. the total records across three regimes.

Explain why the exact final time is included.

**My calculations:**

### Exercise 18: Explain whole-regime splitting

Why is this split scientifically stronger than randomly assigning individual
time points?

~~~text
train:      complete unipolar pulse
validation: complete lower-amplitude pulse
test:       complete bipolar pulse
~~~

What leakage would occur if 19 s were in training and 20 s from the same
trajectory were treated as an independent test example?

**My explanation:**

### Exercise 19: Audit hidden parameter leakage

Read `ContactResistanceRegimeDataset` and
`ContactResistanceDatasetSplit`.

1. Which fields do they contain?
2. Do they contain the true resistance?
3. Where is current information stored?
4. Where are sensor locations and units stored?
5. When is the true value allowed to reappear for scoring?

**My audit:**

### Exercise 20: Explain why observations are ideal first

Why are noise, bias, lag, and missingness disabled in the first recovery?

For each imperfection, name one way it could obscure a problem in the
optimizer or physical parameterization.

**My explanation:**

### Checkpoint 4

Ask Codex to review Exercises 16–20 before studying the loss function.

---

## Block 5 — Derive the fitting objective

### Exercise 21: Select the fitted sensors

Explain why the cold face and cold exchanger are the first two sensors used to
infer cold contact resistance.

Why are the hot sensors stored but excluded from the fitting loss?

**My explanation:**

### Exercise 22: Derive the mean squared error

Write the equal-weight loss over 61 times and two fitted sensors:

$$
L(r)=\frac{1}{122}
\sum_{s\in\{cf,cx\}}\sum_{k=1}^{61}
\left[T_{s,k}^{pred}(r)-T_{s,k}^{obs}\right]^2.
$$

1. Why is the denominator 122?
2. What are the loss units?
3. What does exact zero mean in this synthetic experiment?
4. Why would exact zero be unrealistic with hardware data?

**My derivation:**

### Exercise 23: Predict the sensitivity sweep

Before running it, rank the expected training losses at:

- 0.10 K/W;
- 0.25 K/W; and
- 0.50 K/W.

Which should be exactly zero? Must the low- and high-candidate losses be
symmetric around the true value? Explain.

**My prediction:**

### Exercise 24: Distinguish sensitivity and identifiability

Explain why visibly different curves at different resistances establish local
sensitivity but do not prove practical identifiability if other parameters
are also uncertain.

Give examples involving:

- cold-face capacitance;
- cold reservoir conductance;
- sensor lag; and
- fixed cold-face bias.

**My explanation:**

### Exercise 25: Design alternative weighting

Propose how the loss might change if:

1. sensors have different known noise levels;
2. transient times should receive more emphasis;
3. one sensor has missing records; or
4. temperature errors are temporally correlated.

Why is equal weighting acceptable only as a first ideal baseline?

**My design:**

### Checkpoint 5

Ask Codex to review Exercises 21–25 before studying the scalar optimizer.

---

## Block 6 — Understand golden-section search

### Exercise 26: Explain why a scalar search is enough

Why does the first conventional estimator not require:

- a neural network;
- automatic differentiation;
- a multidimensional optimizer; or
- an initial parameter guess?

What changes when two contact resistances are inferred simultaneously?

**My explanation:**

### Exercise 27: Check the search bounds

The search interval is 0.05 to 1.0 K/W.

1. Why must the lower bound be positive?
2. Does the interval contain the hidden truth?
3. What would it mean if the best estimate landed at 0.05 K/W?
4. How could an overly narrow interval create false confidence?

**My analysis:**

### Exercise 28: Trace one golden-section iteration

Starting with interval $[a,b]$, explain how the two interior points are
selected and how comparing their losses allows one side of the interval to be
discarded.

Why can one previous loss evaluation be reused on the next iteration?

**My explanation:**

### Exercise 29: Interpret stopping criteria

The frozen configuration uses:

- resistance tolerance 1e-8 K/W; and
- at most 96 iterations.

Explain the purpose of both rules. Why should the implementation stop if
either rule is reached?

**My explanation:**

### Exercise 30: Audit the search history

Read `fit_cold_contact_resistance`.

1. Where is each candidate recorded?
2. Where is each MSE recorded?
3. Are candidates allowed outside the bounds?
4. Can validation or test datasets enter the fitter?
5. Why is keeping the complete search history useful?

**My code trace:**

### Checkpoint 6

Ask Codex to review Exercises 26–30 before tracing the full implementation.

---

## Block 7 — Trace the implementation

### Exercise 31: Trace regime construction

Read `reference_contact_resistance_regimes`.

For each regime, record:

- name;
- split;
- transition times; and
- current values.

Verify that the schedules use the right-continuous control class.

**My code trace:**

### Exercise 32: Trace candidate experiment construction

Read `contact_resistance_experiment`.

1. Which reference experiment is copied?
2. Which thermal parameter is replaced?
3. Which current schedule is replaced?
4. Which physical quantities remain unchanged?
5. Where is positivity checked?

**My code trace:**

### Exercise 33: Trace observation generation

Read `simulate_contact_resistance_observations`.

1. Where is RK4 executed?
2. Which object contains the dense trajectory temporarily?
3. Where are observations sampled?
4. Does the returned dataset contain dense truth?
5. How is the measurement interval selected?

**My code trace:**

### Exercise 34: Trace paired errors

Read `_paired_temperature_errors`.

1. Why must predicted and observed times match exactly?
2. In what order are sensor errors appended?
3. What happens if there are no paired temperatures?
4. Why is this helper separate from the optimizer?

**My code trace:**

### Exercise 35: Trace held-out evaluation

Read `evaluate_contact_resistance_regime`.

1. Which four per-sensor RMSE values are calculated?
2. What enters `fitted_pair_rmse`?
3. What enters `all_sensor_rmse`?
4. Why are both useful?

**My code trace:**

### Exercise 36: Trace the high-level experiment

Read `run_contact_resistance_inference_experiment` and draw its call graph.
Include:

- dataset generation;
- fitting;
- sensitivity evaluation;
- parameter scoring;
- training metrics;
- validation metrics; and
- test metrics.

Mark the point after which hidden truth may be used for validation.

**My call graph:**

### Checkpoint 7

Ask Codex to review Exercises 31–36 before examining numerical results.

---

## Block 8 — Analyze the numerical results

### Exercise 37: Run the experiment

Run:

~~~bash
python3 -m thermotwin.contact_resistance_inference
~~~

Record:

- inferred resistance;
- relative parameter error;
- search evaluations;
- training RMSE;
- validation RMSE; and
- test RMSE.

**My result:**

### Exercise 38: Verify the training transient

Print the cold-face and cold-exchanger observations at 0, 5, 6, 10, 15, 20,
21, 30, and 60 s.

1. At which time is the sampled contact gap largest?
2. At which time is the cold face coldest?
3. Why is the recorded current already 0 A at 20 s?
4. Why does the contact gap remain nonzero after turn-off?

**My table and interpretation:**

### Exercise 39: Verify resistance sensitivity at 20 s

Run the training regime at 0.10, 0.25, and 0.50 K/W. Record the cold face,
cold exchanger, and contact gap at 20 s.

Compare the result with your Exercise 13 prediction. Correct any mistaken
assumption about fixed heat rate versus fixed temperature difference.

**My results:**

### Exercise 40: Interpret near-zero errors

The parameter and temperature errors are near floating-point precision.

Explain why this does **not** mean:

- the model has nanokelvin hardware accuracy;
- a physical contact resistance can be known to nine decimal places;
- the fixed parameters are correct; or
- the inverse problem will remain easy after adding noise.

Use the phrase `same-model synthetic baseline` or `inverse crime` correctly.

**My interpretation:**

### Exercise 41: Evaluate transfer to unseen regimes

Why do low validation and bipolar-test errors provide a stronger software
check than training error alone?

Why do they still not constitute broad empirical generalization?

**My explanation:**

### Checkpoint 8

Ask Codex to review Exercises 37–41 before adding observation imperfections.

---

## Block 9 — Predict measurement-imperfection effects

### Exercise 42: Add Gaussian noise conceptually

Predict how independent 0.05 K noise would change:

- the minimum training loss;
- the fitted resistance;
- repeated estimates across seeds; and
- the appropriate loss weighting.

Would one noisy trial be enough to quantify uncertainty?

**My prediction:**

### Exercise 43: Add fixed bias conceptually

Suppose only the cold-face sensor has +0.10 K bias.

1. Which contact gap is systematically altered?
2. Which direction might the resistance estimate move?
3. Why is the direction worth verifying numerically rather than guessing?
4. Why will averaging more time points not remove the error?

**My prediction:**

### Exercise 44: Add sensor lag conceptually

Suppose the cold-face sensor has a 2 s lag.

1. How can lag resemble extra thermal capacitance?
2. Which parts of the pulse are most affected?
3. Why could an inference method compensate with a wrong contact resistance?
4. What independent calibration would help?

**My analysis:**

### Exercise 45: Add missing observations conceptually

Remove cold-face readings from 20 through 30 s.

1. Which key event occurs at the beginning of that interval?
2. Does the thermal trajectory change?
3. Which resistance-sensitive information is lost?
4. Why may 11 missing records remove more than 11/244 of useful information?

**My analysis:**

### Exercise 46: Design the staged robustness study

Put these extensions in an order that isolates causes:

- noise;
- bias;
- lag;
- missing readings;
- multiple uncertain parameters; and
- model mismatch.

For every stage, name the result from the previous stage that must remain as a
limiting-case test.

**My study design:**

### Checkpoint 9

Ask Codex to review Exercises 42–46 before implementing robustness trials.

---

## Block 10 — Identifiability, limitations, and next experiments

### Exercise 47: Construct a parameter-confounding table

For each quantity, explain one way an incorrect value could be compensated by
an incorrect cold contact resistance:

| Quantity | Possible confounding mechanism |
| --- | --- |
| Cold-face capacitance |  |
| Cold-exchanger capacitance |  |
| Cold reservoir conductance |  |
| Module thermal conductance |  |
| Cold-face bias |  |
| Cold-face lag |  |

**My table:**

### Exercise 48: Propose a profile-loss analysis

Describe how you would evaluate training loss across a dense grid of fixed
resistance values.

1. What does a sharp minimum suggest?
2. What does a flat valley suggest?
3. How would noise change the curve?
4. Why is optimizer convergence not the same as identifiability?

**My plan:**

### Exercise 49: Choose the next informative experiment

Propose one new current schedule that is not already in the three frozen
regimes. State:

- amplitude;
- transition times;
- duration;
- sensors;
- sampling interval; and
- the ambiguity it is intended to reduce.

Explain how you would compare its predicted information with the existing
pulses before running hardware.

**My proposed experiment:**

### Exercise 50: State hardware requirements

Before applying any schedule to hardware, list required decisions about:

- allowable current and voltage;
- temperature limits;
- current-driver behavior;
- sensor placement and calibration;
- sampling synchronization;
- contact assembly and clamping;
- reservoir conditions;
- emergency shutdown; and
- repeatability.

Which of these are absent from the synthetic software experiment?

**My checklist:**

### Checkpoint 10

Ask Codex to review Exercises 47–50 before extending the estimator or planning
a physical trial.

---

## Block 11 — Trace the implemented Gaussian-noise study

### Exercise 51: Predict the parameter distribution from the physics

Before running or reading the frozen results, consider many repetitions of the
same experiment with independent, zero-mean temperature noise.

1. Should every fitted resistance equal the truth? Why or why not?
2. Should the mean fitted resistance necessarily equal the truth exactly for
   a finite number of trials?
3. Sketch the distribution you expect around 0.25 K/W.
4. Predict whether fitting both cold temperatures should be more stable than
   fitting only the contact temperature difference. Consider independent
   noise in both sensors.
5. Explain why zero-mean temperature noise does not mathematically guarantee
   zero parameter bias in a nonlinear inverse problem.

**My prediction:**

### Exercise 52: Reconstruct the seed map

Open `contact_resistance_noise_study.py` and find
`contact_resistance_noise_seeds`.

1. Write the train, validation, and test seeds for trial indices 0, 1, and 2.
2. Derive the three formulas for trial index $i$.
3. Prove that no two regimes among the first 100 trials reuse a seed.
4. Explain why using the same seed for all three regimes would weaken the
   independence of the evaluation.
5. Identify the test that checks reproducibility and non-overlap.

**My seed table and explanation:**

### Exercise 53: Derive and test the zero-noise limit

Set the noise standard deviation to 0 K in your reasoning.

1. What should happen to every observation?
2. What should happen to observation RMSE versus truth RMSE?
3. Why might the inferred resistance differ from 0.25 K/W by a tiny amount
   even though the data are exact?
4. Find the search tolerance used by the noise study and compare it with the
   tighter tolerance in the ideal experiment.
5. Find the two tests that enforce the dataset and inference limiting cases.

**My limiting-case derivation:**

### Exercise 54: Trace one trial through the code

Starting at `run_contact_resistance_noise_trial`, write the exact function path
for:

~~~text
ideal split -> noisy split -> training fit -> regime evaluation -> trial record
~~~

For each step, state:

- the type of the input and output object;
- whether the object is ideal, noisy, or predicted;
- which sensors it contains;
- which sensors enter the fitting loss; and
- whether it is permitted to expose hidden truth to the estimator.

Then locate the line that prevents validation or test data from entering the
fit. Is that safeguard implemented in the noise-study module or inherited
from the original inference module?

**My code trace:**

### Exercise 55: Separate observation error from truth error

For a fitted prediction $T^{pred}$, noisy reading $T^{noisy}$, and hidden ideal
temperature $T^{ideal}$:

1. Write $RMSE_{obs}$.
2. Write $RMSE_{truth}$.
3. Which one could be computed in a physical experiment?
4. Which one measures error in the modeled physical trajectory in this
   synthetic experiment?
5. Why can $RMSE_{truth}$ be much smaller than $RMSE_{obs}$ without data
   leakage or overfitting?
6. Find `_single_group_fitted_pair_rmse`. Explain why it is called once with
   noisy datasets and once with ideal datasets.

**My explanation:**

### Exercise 56: Reproduce the parameter summary by hand

Suppose five trials return resistance estimates $r_1,\ldots,r_5$.

1. Write the formula for mean inferred resistance.
2. Write the signed mean bias relative to 0.25 K/W.
3. Write parameter RMSE.
4. Write the sample standard deviation and explain why its denominator is
   $n-1$ rather than $n$ in this report.
5. Explain why RMSE includes both spread and bias.
6. Trace each formula to
   `summarize_contact_resistance_noise_trials`.
7. Read `_percentile` and calculate the interpolation positions for the 5th
   and 95th percentiles when $n=100$.

**My derivation and code mapping:**

### Exercise 57: Interpret the frozen 100-trial result

Run:

~~~bash
python3 -m thermotwin.contact_resistance_noise_study
~~~

Record the output, then answer:

1. How large is the mean bias compared with the sample standard deviation?
2. What percentage of the 0.25 K/W truth is the sample standard deviation?
3. Does the empirical 5th--95th percentile interval contain the truth?
4. What do zero bound hits rule out, and what do they not prove?
5. Why are the observation RMSEs close to 0.05 K?
6. Why do validation and bipolar-test truth RMSE differ even though both use
   the same noise standard deviation?
7. Is the percentile range a hardware confidence interval? State the exact
   limitations in your own words.

**My result and interpretation:**

### Exercise 58: Audit and extend the tests

Open `tests/test_contact_resistance_noise_study.py`.

1. Match each test to one of these categories: input validation,
   reproducibility, limiting case, data-schema preservation, numerical
   regression, statistical calculation, or reporting.
2. Explain why the regular test suite uses five trials instead of rerunning
   the 100-trial study every time.
3. Add a written proposal for a test of noise scales 0, 0.01, 0.05, and 0.10 K.
   State the trend you expect in parameter RMSE without demanding exact
   monotonicity from a small random sample.
4. Propose a separate experiment for temporally correlated noise. Do not add
   it to the current independent-noise implementation.
5. Name one failure that could pass a mean-estimate check but be caught by the
   seed, schema, truth-RMSE, or bound-hit checks.

**My audit and extension proposal:**

### Checkpoint 11

Ask Codex to review Exercises 51–58. In particular, ask for checks of the
finite-sample interpretation, the difference between observation and truth
errors, and any claim that sounds stronger than the synthetic experiment
supports.

---

## Block 12 — Fixed bias and systematic parameter error

### Exercise 59: Predict individual bias directions

Before running the bias study, consider the measured cold contact gap
$T_{cx}^{observed}-T_{cf}^{observed}$.

1. How does +0.10 K cold-face bias change this measured gap?
2. How does +0.10 K cold-exchanger bias change it?
3. Predict which bias should make the fitted resistance larger and which
   should make it smaller.
4. Explain why the full answer also depends on absolute temperatures and the
   coupled transient, not only the instantaneous gap.

**My prediction:**

### Exercise 60: Analyze common-mode and differential bias

For these two patterns,

- common mode: $b_{cf}=b_{cx}=+0.10$ K;
- differential: $b_{cf}=+0.05$ K and $b_{cx}=-0.05$ K,

answer:

1. Which pattern preserves the contact temperature difference?
2. Which changes it by -0.10 K?
3. Why can common-mode bias still alter a loss based on both absolute
   temperatures?
4. Under what alternative loss would common-mode bias cancel exactly?
5. What physical information would that alternative loss discard?

**My analysis:**

### Exercise 61: Trace and interpret the bias code

Open `contact_resistance_bias_study.py`.

1. Trace one case from ideal split through `apply_fixed_temperature_bias`,
   fitting, and held-out evaluation.
2. Verify that physical parameters and current schedules are unchanged.
3. Run the module and record all five inferred resistances.
4. Compare signed parameter error with train, validation, and test truth RMSE.
5. Explain why more trials would not remove these deterministic shifts.

**My trace and interpretation:**

### Exercise 62: Audit bias limiting cases and claims

Open `tests/test_contact_resistance_bias_study.py`.

1. Find the exact zero-bias limiting-case test.
2. Find the test enforcing opposite face/exchanger parameter directions.
3. Explain why a frozen numerical regression is useful here.
4. State what this study establishes and what it does not establish about
   physical sensor calibration.

**My audit:**

### Checkpoint 12

Ask Codex to review Exercises 59–62 for contact-gap signs, common-mode
reasoning, and claims about averaging systematic errors.

---

## Block 13 — Sensor lag and contact-dynamics confusion

### Exercise 63: Derive the first-order lag update

Start with

$$
\frac{dT_s}{dt}=\frac{T_{target}-T_s}{\tau_s}.
$$

Assuming the target is constant over one step:

1. Derive the exact update used in the code.
2. Evaluate the decay factor for $\Delta t=0.1$ s and $\tau_s=2$ s.
3. Evaluate it again for $\Delta t=1$ s.
4. Explain why evolving only at 1 s output times defines a different sensor
   response from evolving at 0.1 s and then sampling.
5. State the limits as $\tau_s\to0$ and as $\tau_s\to\infty$.

**My derivation:**

### Exercise 64: Trace dense-before-sparse lag

Trace `lag_contact_resistance_dataset_split` in
`contact_resistance_robustness.py`.

1. Where is dense truth regenerated for each current regime?
2. Where is the sensor state evolved?
3. Where is the result downsampled?
4. Which metadata and current histories are preserved?
5. Which test proves the zero-lag dense pipeline equals ideal 1 s data?

**My code trace:**

### Exercise 65: Interpret lag as a confounder

Run `contact_resistance_lag_study.py` and answer:

1. Why do face-only and exchanger-only lag move resistance differently?
2. Why does common 2 s lag not cancel?
3. Why can resistance reduce some lag error without eliminating it?
4. Why is bipolar-test observation RMSE useful for detecting mismatch?
5. How could a trainable capacitance be confused with sensor lag?
6. What additional experiment might help distinguish the two?

**My interpretation:**

### Exercise 66: Review the lag tests and limitations

Classify each test in `test_contact_resistance_lag_study.py` as a configuration,
limiting-case, direction, regression, transfer, or reporting check. Then state
why this study demonstrates a risk of capacitance confounding without actually
quantifying joint capacitance-lag identifiability.

**My review:**

### Checkpoint 13

Ask Codex to review Exercises 63–66 for the lag equation, ordering, and the
difference between demonstrating confounding and identifying two parameters.

---

## Block 14 — Informative missing readings

### Exercise 67: Locate every turn-off from code

For each frozen regime, inspect `transition_times` and `values`.

1. List every transition where current changes from nonzero to zero.
2. Verify the training, validation, and bipolar-test turn-off times.
3. Explain why the code derives these times instead of hard-coding 20 s for
   every regime.
4. Predict how many cold-pair readings remain for instant, plus-or-minus 2 s,
   and plus-or-minus 5 s training outages.

**My transition table:**

### Exercise 68: Derive the information-curvature metric

The study computes local curvature of training SSE rather than MSE.

1. Write the centered second-difference formula.
2. State the units of the numerator, denominator, and curvature.
3. Explain why multiplying MSE by available-record count matters when cases
   contain different numbers of records.
4. Predict the curvature effect of removing equilibrium readings whose model
   sensitivity to resistance is zero.
5. State why curvature is not a confidence interval.

**My derivation:**

### Exercise 69: Compare equal-count missingness designs

The equilibrium-control and plus-or-minus 2 s cases both retain 112 training
records.

1. Record both curvature values.
2. Compute each as a fraction of complete-data curvature.
3. Explain physically why the switch-adjacent case loses more information.
4. Why does every case still recover the exact parameter?
5. Predict what would happen to trial spread if 0.05 K noise were added.

**My comparison:**

### Exercise 70: Trace missing-record pairing

Inspect the generalized `_paired_temperature_errors` and the missingness study.

1. How are predictions matched to retained readings?
2. Why are missing values not filled with zero, `NaN`, or interpolation?
3. How does `match_split_schema` prevent hidden ideal records from entering
   truth RMSE at unavailable times?
4. Identify tests for transition alignment, counts, curvature, and exact
   recovery.

**My code audit:**

### Checkpoint 14

Ask Codex to review Exercises 67–70 for switch timing, SSE normalization, and
the distinction between exact recovery and practical information.

---

## Block 15 — Restricted sensors and practical identifiability

### Exercise 71: Predict sensor-set ranking

Rank these sets before running the code:

- cold face only;
- cold exchanger only;
- cold pair;
- hot pair; and
- all four sensors.

Explain the physical path by which cold contact resistance influences each
location. State which pair measures directly across the contact and which
responds only through the coupled thermal system.

**My ranking and reasoning:**

### Exercise 72: Separate exact recovery from information

After running `contact_resistance_sensor_study.py`:

1. Why does every exact case recover 0.25 K/W?
2. Compute the face-only to exchanger-only curvature ratio.
3. Compute hot-pair curvature as a percentage of cold-pair curvature.
4. Compute the percentage curvature added by hot sensors to the cold pair.
5. Which result would you use for sensor selection, and why is exact recovery
   alone inadequate?

**My calculations:**

### Exercise 73: Trace physical schema restriction

Inspect `restrict_observation_dataset`.

1. What happens to sensor definitions?
2. What happens to long-form records?
3. Which units and sampling metadata remain?
4. How does the fitter reject an unavailable selected sensor?
5. Why is filtering only the loss while retaining a hidden sensor a weaker
   representation of physical availability?

**My trace:**

### Exercise 74: Design a hardware sensor decision

Suppose only one cold-side sensor can be installed.

1. Which location does this synthetic study favor?
2. List at least four hardware factors absent from curvature alone.
3. Propose a current schedule that could improve exchanger-only sensitivity.
4. Explain how you would compare candidate schedules before hardware testing.

**My design:**

### Checkpoint 15

Ask Codex to review Exercises 71–74 for the sensitivity path, numerical ratios,
and any sensor recommendation stated more strongly than the synthetic model
supports.

---

## Block 16 — Combined measurement imperfections

### Exercise 75: Defend the transformation order

For the implemented pipeline

~~~text
dense truth -> lag -> sample -> bias -> noise -> missing -> restrict
~~~

explain:

1. Why lag must occur before sampling.
2. Why bias and noise act on reported temperature values.
3. Why missingness occurs after generating the readings.
4. Why restricting sensors last preserves the agreed random sequence.
5. Which pairs of transformations would commute mathematically and which
   would change results if reversed.

**My explanation:**

### Exercise 76: Reconstruct the complete limiting case

Configure:

- zero noise;
- zero bias;
- zero lag;
- no turn-off outage; and
- the normal cold fitting pair.

Predict every summary metric. Then find the test that enforces recovery below
1e-6. Explain why a limiting case of the combined machinery is more valuable
than testing each transformation only in isolation.

**My prediction and test trace:**

### Exercise 77: Analyze systematic error versus random spread

For the 100-trial combined result:

1. Record mean estimate, mean bias, sample standard deviation, and RMSE.
2. Compute $|bias|/standard\ deviation$.
3. Compare the combined mean and spread with the noise-only study using the
   same seeds.
4. Explain why the combined empirical interval misses 0.25 K/W.
5. Would 1,000 trials correct this bias? What would improve instead?

**My analysis:**

### Exercise 78: Audit observation and truth errors

1. Record mean train, validation, and test observation RMSE.
2. Record the corresponding visible-truth RMSE.
3. Explain why visible truth uses only keys that remain available after
   missingness and restriction.
4. Why is bipolar-test error largest?
5. Identify one combined-study conclusion supported by the evidence and three
   claims that would still be unjustified for hardware.

**My audit:**

### Checkpoint 16

Ask Codex to review Exercises 75–78 for pipeline order, limiting cases,
systematic-versus-random interpretation, and hardware caveats.

---

## Interview teach-back

### 30-second explanation

Explain why a current pulse helps identify thermal contact resistance.

**My answer:**

### Two-minute explanation

Explain the complete path from frozen current regimes through RK4 truth,
ideal observations, whole-experiment splitting, cold-pair least squares,
golden-section search, held-out validation, independent noisy repetitions, and
empirical parameter statistics. Continue through isolated bias, dense sensor
lag, regime-aligned missingness, restricted sensor sets, and the combined
pipeline. State why neither the near-zero ideal errors nor any synthetic
percentile range establishes hardware accuracy.

**My answer:**

### Challenge questions

1. Why do temperatures remain continuous when current switches?
2. Why can temperature derivatives change immediately?
3. Why does a larger resistance create a larger driven contact gap here?
4. Why are both temperatures across the contact valuable?
5. Why exclude hot-side readings from the fitting loss but retain them?
6. Why split by experiment rather than time point?
7. Why is exact synthetic recovery necessary but insufficient?
8. Why can sensor lag be confused with thermal capacitance?
9. Why can missing switch-time data be especially damaging?
10. What would make the resistance practically unidentifiable?
11. Why do zero-mean sensor errors not guarantee zero parameter bias?
12. Why must observation RMSE and hidden-truth RMSE be interpreted separately?
13. Why is an empirical percentile range not automatically a confidence
    interval for hardware?
14. Why does common-mode cold-sensor bias not cancel from this loss?
15. Why must lag be evolved before sparse output sampling?
16. Why can sensor lag be confused with contact resistance or capacitance?
17. Why can two missing-data cases with equal record counts carry different
    information?
18. Why can exact recovery coexist with extremely weak practical sensitivity?
19. Why do additional hot-side sensors add little cold-contact information in
    the frozen experiment?
20. Why do more Monte Carlo trials fail to correct systematic bias?

**My answers:**

---

## Corrections log

| Exercise | My original mistake | Consequence | Corrected understanding |
| --- | --- | --- | --- |
|  |  |  |  |

## Questions for review

1.
2.
3.
