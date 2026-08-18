# 13 — Measurement imperfections and missing observations

Status: `Not started`

## Purpose

The thermal solver predicts modeled node temperatures. The virtual test stand
turns those hidden predictions into sensor records. This sheet studies the
measurement effects added after the original ideal-observation exercise:

1. independent Gaussian temperature noise;
2. fixed sensor bias;
3. first-order sensor lag; and
4. missing observations.

All four mechanisms are now implemented as separate, composable observation
transformations. The missing-observation baseline follows the deterministic
outage assumptions introduced in this sheet.

Two cross-cutting developments also belong in this sheet:

- the distinction between truth-integration resolution and measurement
  sampling resolution; and
- the order in which lag, sampling, bias, noise, and missingness are applied.

The relevant implemented files are:

- `thermotwin/virtual_test_stand.py`;
- `thermotwin/measurement_noise.py`;
- `thermotwin/measurement_bias.py`;
- `thermotwin/measurement_lag.py`;
- `thermotwin/measurement_missingness.py`;
- `tests/test_virtual_test_stand.py`;
- `tests/test_measurement_noise.py`;
- `tests/test_measurement_bias.py`; and
- `tests/test_measurement_lag.py`; and
- `tests/test_measurement_missingness.py`.

Make predictions before evaluating code. Explain every quantity with units,
and distinguish a physical-model change from an observation-model change.

---

## Current baselines

| Mechanism | Generic learning baseline | State |
| --- | --- | --- |
| Sampling | Four sensors, every 1 s from 0 through 60 s | Implemented |
| Temperature noise | Independent Gaussian, 0.05 K standard deviation, seed 2026 | Implemented |
| Fixed bias | Cold-face offset of +0.10 K | Implemented |
| Sensor lag | Cold-face time constant of 2 s | Implemented |
| Missing readings | Cold-face outage from 20 through 30 s, inclusive | Implemented |

These are controlled synthetic values. They are not calibrated properties of
physical hardware.

The implemented complete pipeline is:

~~~text
dense thermal truth
    -> first-order sensor lag
    -> output sampling
    -> fixed sensor bias
    -> independent readout noise
    -> remove unavailable readings
~~~

---

## Block 1 — Classify the mechanisms

### Exercise 1: Separate physical state from reported data

For each item, decide whether it changes the four thermal state equations,
the observation dataset, or both:

1. increasing module thermal conductance;
2. increasing cold contact resistance;
3. increasing temperature-noise standard deviation;
4. adding a fixed sensor bias;
5. adding first-order sensor lag without thermal loading;
6. deleting an unavailable reading; and
7. adding a physical sensor bead with heat capacity and thermal contact.

Explain why the current lag implementation belongs to a different category
from a physically coupled sensor bead.

**My classification:**

### Exercise 2: Identify dimensions and units

State the units of:

- temperature $T$;
- temperature error $e$;
- noise standard deviation $\sigma$;
- fixed bias $b_s$;
- lag time constant $\tau_s$;
- sampling interval $\Delta t_m$; and
- missing-reading probability, if a future random model uses one.

Which of these quantities are dimensionless?

**My unit table:**

### Exercise 3: Compare error signatures

Describe the pattern you would expect in a temperature-error-versus-time plot
for each mechanism:

1. independent zero-mean noise;
2. constant positive bias;
3. first-order lag during cooling and heating; and
4. a temporary communication outage.

Which mechanisms create incorrect numeric values, and which creates no value
at all?

**My comparison:**

### Exercise 4: Protect hidden truth

Explain why synthetic validation may compare a reported temperature with
hidden truth, but a parameter-inference routine must not silently receive the
dense truth trajectory.

Would keeping a truth value beside every missing reading create a risk of
information leakage? Explain.

**My explanation:**

### Checkpoint 1

Ask Codex to review Exercises 1–4 before running measurement transformations.

---

## Block 2 — Temperature noise

### Exercise 5: Write the noise equation

Use

$$
T_{m,s,k}=T_{\mathrm{input},s,k}+\epsilon_{s,k},
\qquad
\epsilon_{s,k}\sim\mathcal N(0,\sigma_s^2).
$$

1. Explain each subscript.
2. State the expected error mean and variance.
3. Must one finite realization have exactly zero mean?
4. Why is $\sigma_s$ measured in kelvin rather than kelvin squared?
5. What quantity has units of square kelvin?

**My derivation:**

### Exercise 6: Predict the zero-noise limit

Set every standard deviation to 0 K.

1. Which temperature values should be returned?
2. Should time, current, location, or record count change?
3. Why should this test use exact equality rather than a statistical
   tolerance?
4. Find the automated test that enforces this limit.

**My prediction and test:**

### Exercise 7: Explain reproducible randomness

1. Why do two runs with seed 2026 match exactly?
2. Why does another seed produce another synthetic trial?
3. Why is one seed useful for regression testing but inadequate for an
   uncertainty study?
4. What statistics would you collect over many seeds?

**My explanation:**

### Exercise 8: Analyze averaging

For $N$ independent readings with standard deviation $\sigma$, the standard
deviation of their mean is

$$
\sigma_{\bar T}=\frac{\sigma}{\sqrt{N}}.
$$

1. Calculate this value for $\sigma=0.05$ K and $N=1$, 4, 25, and 100.
2. What independence assumption is required?
3. Why would temporally correlated noise reduce the benefit of averaging?
4. Does this averaging rule remove a constant sensor bias?

**My calculations:**

### Exercise 9: Trace the noise code

Read `GaussianTemperatureNoise` and
`apply_gaussian_temperature_noise`.

1. Which settings are validated?
2. Which observation field is replaced?
3. Why are named overrides checked against known sensors?
4. Why is a new dataset returned?
5. Why is the configuration retained with the result?

**My code trace:**

### Checkpoint 2

Ask Codex to review Exercises 5–9 before comparing noise with bias.

---

## Block 3 — Fixed sensor bias

### Exercise 10: Write the bias equation

For sensor $s$, use

$$
T_{m,s,k}=T_{\mathrm{input},s,k}+b_s.
$$

1. Why does $b_s$ have a sensor subscript but not a time subscript?
2. What does a positive bias mean?
3. Can a physically valid bias be negative?
4. Why must the configured value be finite?

**My explanation:**

### Exercise 11: Predict the frozen bias baseline

The cold-face sensor has $b_c=+0.10$ K. Every other bias is 0 K.

Predict:

1. all four readings at time zero;
2. the cold-face error at every time;
3. the mean cold-face error;
4. which metadata fields change; and
5. whether the physical cold-face temperature changes.

**My predictions:**

### Exercise 12: Distinguish bias from a model error

Suppose the measured cold face remains warmer than the model prediction.
Explain how this discrepancy could arise from:

- positive sensor bias;
- incorrect contact resistance;
- incorrect thermal conductance;
- incorrect external heat input; or
- incorrect sensor location.

Why is it dangerous to infer a physical parameter while assuming every
systematic discrepancy is physics?

**My analysis:**

### Exercise 13: Design a calibration check

Propose a uniform known-temperature experiment for estimating sensor offsets.

1. What reference condition or instrument is required?
2. How many repeated readings would you collect?
3. How would you separate scatter from offset?
4. Why might the apparent bias depend on temperature?
5. Why is the implemented +0.10 K not a calibration result?

**My experiment:**

### Exercise 14: Trace the bias code and tests

Read `FixedTemperatureBias`, `apply_fixed_temperature_bias`, and
`tests/test_measurement_bias.py`.

Map each claim to a test:

| Claim | Test |
| --- | --- |
| Zero bias reproduces input |  |
| Only the selected sensor changes |  |
| Bias persists across time |  |
| Unknown override names are rejected |  |
| Input data is not mutated |  |

**My test map:**

### Checkpoint 3

Ask Codex to review Exercises 10–14 before analyzing dynamic lag.

---

## Block 4 — First-order sensor lag

### Exercise 15: Derive the response direction

The implemented observation model starts from

$$
\tau_s\frac{dT_{m,s}}{dt}
=T_{\mathrm{input},s}-T_{m,s}.
$$

1. Determine the sign of $dT_{m,s}/dt$ when the input is warmer.
2. Determine the sign when the input is colder.
3. Show that both sides have units of kelvin.
4. What happens at equilibrium?
5. What do the limits $\tau_s\to0$ and $\tau_s\to\infty$ mean?

**My derivation:**

### Exercise 16: Calculate a discrete update

For a constant target during one interval, the code uses

$$
a=\exp\left(-\frac{\Delta t}{\tau_s}\right),
$$

$$
T_{m,k}=aT_{m,k-1}+(1-a)T_{\mathrm{input},k}.
$$

Use $\tau_s=2$ s, $\Delta t=1$ s, $T_{m,k-1}=300$ K, and
$T_{\mathrm{input},k}=299$ K.

1. Calculate $a$.
2. Calculate $T_{m,k}$.
3. Show that the result lies between the old reading and the target.
4. Repeat with $\tau_s=4$ s.
5. Which sensor responds more slowly, and why?

**My calculations:**

### Exercise 17: Predict lag during the reference transient

The cold face begins cooling while the lagged sensor begins at the exact
initial node temperature.

Predict:

1. the initial error;
2. the later error sign;
3. whether the error grows forever;
4. what happens near steady state; and
5. what happens to the other three sensors, whose time constants are zero.

Then compare your prediction with the documented maximum and final errors.

**My prediction and interpretation:**

### Exercise 18: Explain dense filtering before sampling

Compare:

~~~text
dense truth -> lag -> sample every 5 s
dense truth -> sample every 5 s -> lag
~~~

1. Why can the two sequences differ?
2. Which sequence represents a sensor that continues evolving between logged
   readings?
3. Why does the implementation use the 0.1 s truth history for lag?
4. Is 0.1 s automatically sufficient for every possible sensor time
   constant?
5. What convergence check would you perform for a very fast sensor?

**My explanation:**

### Exercise 19: Distinguish lag from physical loading

1. Does the implemented lag remove energy from a thermal node?
2. Does it add a thermal state to the four-node model?
3. What additional capacitance and conductance terms would a physical sensor
   bead require?
4. Under what conditions is the no-loading approximation plausible?
5. What hardware test could challenge that approximation?

**My explanation:**

### Exercise 20: Trace lag validation

Find tests for:

- zero time constant;
- constant temperature;
- an exponential step response;
- irregular time intervals;
- a larger time constant producing more lag;
- dense filtering before output downsampling; and
- lag occurring before bias and noise.

For each test, state whether it protects physics, numerical behavior, schema,
or transformation order.

**My test map:**

### Checkpoint 4

Ask Codex to review Exercises 15–20 before composing measurement effects.

---

## Block 5 — Composition and order

### Exercise 21: Trace the complete implemented pipeline

Explain every arrow in:

~~~text
dense truth -> lag -> output sampling -> bias -> noise
~~~

For every stage, state:

1. its input;
2. its output;
3. which values may change;
4. which metadata must remain unchanged; and
5. whether the stage has access to hidden truth.

**My pipeline trace:**

### Exercise 22: Decide which operations commute

Compare these pairs:

1. additive fixed bias and additive noise;
2. sensor lag and random noise;
3. sensor lag and output downsampling;
4. deleting records and adding noise to the retained records; and
5. deleting records and interpolating replacements.

For each pair, decide whether reversing the order gives the same scientific
meaning and whether it gives the same numeric dataset.

**My comparison:**

### Exercise 23: Audit provenance

The combined result retains its lag, bias, and noise configurations but does
not expose ideal truth.

1. Why is configuration provenance important?
2. What would be impossible to reproduce if the random seed were lost?
3. Why should a missingness result retain its outage configuration?
4. Which information is appropriate for tests but inappropriate as an input
   to inverse inference?

**My audit:**

### Exercise 24: Design an order-error test

Construct a short artificial temperature history for which

~~~text
lag -> noise
~~~

differs clearly from

~~~text
noise -> lag
~~~

Predict both sequences before evaluating them. Explain which sequence matches
the agreed interpretation of independent readout noise.

**My example:**

### Checkpoint 5

Ask Codex to review Exercises 21–24 before freezing missingness assumptions.

---

## Block 6 — Missing-observation concepts

### Exercise 25: Distinguish absence from a numeric value

Compare representing a missing temperature as:

1. an omitted record;
2. a `NaN` value plus an explicit validity rule;
3. zero kelvin;
4. the most recent valid reading; and
5. a linearly interpolated value.

Which choices preserve that no measurement occurred? Which silently invent a
measurement? Why is zero kelvin especially dangerous?

**My comparison:**

### Exercise 26: Compare missingness mechanisms

Explain these categories in your own words:

- missing completely at random;
- missing at random conditional on recorded information; and
- missing not at random because availability depends on the unavailable
  value itself.

Where would a known communication outage fit? Where might a sensor that fails
only above a temperature threshold fit? Why does the mechanism matter for
inference?

**My explanation:**

### Exercise 27: Freeze the first outage baseline

Consider the proposed rule:

> Omit `cold_face_sensor` readings from 20 through 30 s, inclusive. Keep all
> other readings. The sensor lag state continues evolving while its output is
> unavailable.

Answer the starting questions:

1. How many cold-face readings are removed?
2. Starting from 244 total observations, how many remain?
3. Does the outage change any modeled node temperature?
4. Why might this interval make a thermal parameter harder to identify?
5. How many cold-face readings remain?
6. How many unique measurement times remain in the full dataset, given that
   the other sensors continue reporting?
7. What happens at exactly 20 s and exactly 30 s under an inclusive rule?

**My predictions:**

### Exercise 28: Decide whether the hidden sensor keeps evolving

Compare two interpretations during an outage:

1. the sensor continues responding physically but its readings are not
   logged; and
2. the sensor state is frozen until communication resumes.

Which matches a communication failure? Which might describe a powered-down
sensor? What should the first restored reading look like in each case?

**My interpretation:**

### Exercise 29: Preserve schema without requiring every sensor at every time

The dataset is long-form: each row identifies its own time and sensor.

1. Why can this naturally represent unequal record counts per sensor?
2. Should the cold-face sensor remain in sensor metadata during its outage?
3. Should `observations_for("cold_face_sensor")` return only valid records?
4. Why must downstream code stop assuming a rectangular four-sensor table?
5. What should happen if a configuration removes every record in a dataset?

**My schema design:**

### Exercise 30: Distinguish deletion from imputation

Suppose readings from 20 through 30 s are absent.

1. What assumptions does linear interpolation make across the gap?
2. Why might interpolation hide a current-induced transient?
3. Should imputed values be treated as equally certain as measured values?
4. Why should missingness and imputation be separate transformations?
5. What mask or provenance would an imputation method need to preserve?

**My analysis:**

### Checkpoint 6 — Baseline agreement

Ask Codex to review Exercises 27–30. Confirm or revise:

- the affected sensor;
- the outage start and end times;
- whether the endpoints are inclusive;
- whether rows are omitted;
- whether lag continues through the outage; and
- whether missingness is applied last.

The implementation uses these choices. If your answers imply a different
physical interpretation, revise the assumptions before using the model for an
experiment.

---

## Block 7 — Plan the missingness code and tests

### Exercise 31: Propose a configuration object

Before reading the implementation, list the fields a deterministic outage
configuration requires. Consider:

- sensor name;
- start time;
- end time; and
- boundary convention.

State validation rules for non-finite times, negative times, reversed
intervals, duplicate rules, overlapping rules, and unknown sensor names.

**My proposed configuration:**

### Exercise 32: Write transformation pseudocode

Write pseudocode that:

1. accepts an immutable observation dataset;
2. validates every outage rule;
3. retains only available observations;
4. preserves sensor and unit metadata;
5. returns the outage configuration with the result; and
6. rejects a result with no observations.

Do not replace missing temperatures with numeric values.

**My pseudocode:**

### Exercise 33: Design limiting-case tests

Specify expected inputs and outputs for:

1. no outage rules;
2. an outage outside all observation times;
3. a one-time inclusive outage;
4. the proposed 20–30 s cold-face outage;
5. an unknown sensor name;
6. invalid time bounds;
7. all readings removed; and
8. a combined lag, bias, noise, and outage workflow.

Which cases should return exact equality, and which should raise an error?

**My test designs:**

### Exercise 34: Predict transformation-order tests

If missingness occurs last, predict whether random-number generation should
run for records that are later removed.

1. Would removing rows before applying seeded noise change the noise values
   assigned to later retained rows?
2. Why might this make two supposedly identical trials disagree?
3. Which order matches a sensor that measured a value but failed to transmit
   it?
4. Would a sensor that never performed the measurement require another
   interpretation?

**My prediction:**

### Checkpoint 7

Ask Codex to review Exercises 31–34 before reviewing the missingness code.

---

## Block 8 — Inference and experiment design

### Exercise 35: Analyze information loss

Explain why removing 11 readings does not necessarily remove exactly
11/244 of the experiment's useful information.

How does the answer depend on whether the missing interval contains:

- a rapid transient;
- steady-state behavior;
- a current switch; or
- the only observation of one thermal node?

**My explanation:**

### Exercise 36: Connect missingness to parameter identifiability

For each parameter, predict whether cold-face loss during 20–30 s could be
important and explain why:

- module thermal conductance $K$;
- cold contact resistance;
- hot contact resistance;
- cold-side capacitance; and
- cold-face sensor time constant.

State which other parameters and measurements you assume known.

**My predictions:**

### Exercise 37: Compare outage locations

Compare equal-duration outages at:

- 0–10 s;
- 20–30 s; and
- 50–60 s.

Which is likely to damage transient-parameter inference most? Which might
damage steady-state comparison most? Verify the physical trajectory before
settling on an answer.

**My comparison:**

### Exercise 38: Design a robust experiment

Propose ways to reduce vulnerability to missing readings:

1. redundant sensors;
2. local device buffering;
3. repeated current pulses;
4. repeated experimental trials;
5. health/status channels; and
6. experiment timing chosen for multiple informative windows.

Which changes improve data reliability, and which improve physical
identifiability even when no readings are missing?

**My design:**

### Exercise 39: Avoid biased evaluation

Why should training and validation datasets not be created by randomly
splitting nearby time points from the same transient?

How should evaluation account for:

- different current schedules;
- different outage patterns;
- different random-noise seeds; and
- complete sensor loss in a deployment case?

**My evaluation plan:**

### Checkpoint 8

Ask Codex to review Exercises 35–39 before using incomplete observations for
inverse inference.

---

## Block 9 — Run and interpret validation

### Exercise 40: Run the implemented focused suites

Run:

~~~bash
python3 -m unittest \
  tests.test_virtual_test_stand \
  tests.test_measurement_noise \
  tests.test_measurement_bias \
  tests.test_measurement_lag \
  tests.test_measurement_missingness
~~~

Record the number of tests, skipped tests, and result.

**My test result:**

### Exercise 41: Build a claim-to-test table

Map every claim to an exact test:

| Claim | Test name |
| --- | --- |
| Noise is reproducible for a saved seed |  |
| Zero noise returns exact temperatures |  |
| Bias remains constant over time |  |
| Zero lag returns exact input |  |
| Larger $\tau$ produces slower response |  |
| Lag is evaluated before coarse sampling |  |
| Only intended outage rows disappear |  |
| Missingness does not mutate the input |  |
| The complete pipeline retains its configurations |  |

**My test map:**

### Exercise 42: Interpret what tests cannot establish

Explain why passing every synthetic test does not prove:

- that real noise is independent or Gaussian;
- that sensor bias is constant;
- that lag is first order;
- that the sensor has no thermal loading;
- that missingness is unrelated to temperature; or
- that inferred parameters are identifiable from hardware data.

For each limitation, name one measurement or experiment that would provide
evidence.

**My interpretation:**

---

## Block 10 — Trace the implemented missingness layer

### Exercise 43: Trace one inclusive outage

Read `TemperatureSensorOutage` in `measurement_missingness.py`.

1. Which three values define an outage?
2. Why must both times be finite and nonnegative?
3. Why may the start and end times be equal?
4. How does `includes` make both endpoints inclusive?
5. Why does it use a floating-point tolerance?

Create a one-time outage at 0.3 s and verify that a stored time represented as
0.30000000000000004 s is removed.

**My code trace:**

### Exercise 44: Trace configuration-level validation

Read `DeterministicTemperatureMissingness`.

1. Why are overlapping intervals rejected for one sensor?
2. Why may two different sensors have simultaneous outages?
3. Where are unknown sensor names rejected?
4. Why can an outage outside the experiment be valid?
5. What does `removes` return for a retained observation?

**My code trace:**

### Exercise 45: Verify the frozen reference counts

Run `run_missing_contact_reference_test_stand` and calculate:

1. the original number of cold-face records;
2. the number removed by the inclusive 20–30 s interval;
3. the number of retained cold-face records;
4. the total number of retained records; and
5. the number of unique full-dataset measurement times.

Print the cold-face times immediately before and after the gap. Explain why
the next retained reading occurs at 31 s.

**My calculation and output:**

### Exercise 46: Verify that missingness changes no temperatures

Compare the ideal dataset with the missing-only result.

1. Confirm that every retained observation exactly equals an original
   observation.
2. Confirm that the original dataset still has 244 records.
3. Confirm that every unaffected sensor history is exactly equal.
4. Confirm that sensor definitions, units, and sampling interval remain.
5. Explain why these checks establish an observation-only transformation but
   do not validate real hardware outages.

**My verification:**

### Exercise 47: Trace the complete workflow

Read `run_incomplete_contact_reference_test_stand`.

1. Which helper generates lagged, biased, and noisy complete data?
2. At what point are records removed?
3. Which four configuration objects are returned?
4. Why is the cold-face reading at 31 s the same as in the complete dataset?
5. What would freezing the lag state during the outage change?
6. Why are hidden ideal data not returned?

**My pipeline trace:**

### Exercise 48: Review the missingness tests

Run:

~~~bash
python3 -m unittest tests.test_measurement_missingness
~~~

For each test in `test_measurement_missingness.py`, label its main purpose as:

- configuration validation;
- limiting case;
- boundary behavior;
- schema preservation;
- frozen reference regression;
- transformation ordering; or
- provenance protection.

Choose the three tests you believe prevent the most scientifically damaging
mistakes and defend your choices.

**My test review:**

### Checkpoint 9

Ask Codex to review Exercises 43–48 before using incomplete records in an
inverse problem.

---

## Interview teach-back

### 30-second explanation

Explain why a digital twin needs a measurement model in addition to its
thermal equations.

**My answer:**

### Two-minute explanation

Explain the complete path from contact-aware RK4 truth to lagged, sampled,
biased, noisy, and partially missing temperature records. State which effects
change physics, which change only observations, and which assumptions require
hardware validation.

**My answer:**

### Challenge questions

1. Why is a missing reading not a temperature of zero?
2. Why does fixed bias not average away like independent noise?
3. Why can lag resemble extra thermal capacitance?
4. Why must lag be evaluated before coarse output sampling?
5. Why can seeded noise depend on whether rows are removed before or after it?
6. Why can a short outage cause a large loss of parameter information?
7. When would a long-form dataset be preferable to a rectangular array?
8. What observation assumption would you test first on real hardware?

**My answers:**

---

## Corrections log

| Exercise | My original mistake | Why it matters | Corrected understanding |
| --- | --- | --- | --- |
|  |  |  |  |

## Questions for review

1.
2.
3.
