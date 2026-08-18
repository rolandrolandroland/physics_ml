# 12 — Ideal virtual test stand and observation model

Status: `Not started`

## Purpose

The conventional four-node solver produces a dense synthetic truth
trajectory. A physical experiment does not reveal that complete trajectory.
It produces measurements from named sensors at particular times.

This sheet studies the first ideal observation layer between the physics model
and future parameter-inference code. The initial layer deliberately has no
noise, bias, lag, calibration error, or missing data. Its job is to establish
an explicit dataset schema and verify that node temperatures are sampled
correctly before measurement imperfections are introduced.

The relevant files are:

- `thermotwin/contact_transient.py`: the four-node truth trajectory;
- `thermotwin/contact_experiments.py`: the frozen physical experiment;
- `thermotwin/virtual_test_stand.py`: sensor definitions, sampling,
  interpolation, and the ideal reference dataset;
- `tests/test_virtual_test_stand.py`: schema, timing, interpolation, current,
  and validation checks; and
- `thermotwin/README_detailed.md`: the full package-level explanation.

Make predictions before running code. Include units in calculations. Preserve
incorrect predictions in the corrections table and explain their consequence.

---

## Frozen ideal baseline

The first virtual test stand uses:

| Choice | Baseline |
| --- | --- |
| Physical truth model | Four-node contact-aware RK4 model |
| Truth integration step | 0.1 s |
| Experiment duration | 60 s |
| Measurement interval | 1.0 s |
| First and last measurement | 0 s and 60 s |
| Sensors | Cold face, hot face, cold exchanger, hot exchanger |
| Temperature unit | K |
| Current unit | A |
| Time unit | s |
| Noise | None |
| Bias | None |
| Lag | None |
| Missing measurements | None |
| Sensor response | Exact node temperature at the requested time |

The four-sensor baseline is a software-validation experiment. It does not
claim that a future hardware test stand will have four accessible, perfectly
placed, ideal sensors.

---

## Block 1 — Separate truth, numerical solution, and observation

### Exercise 1: Define three different objects

Explain the difference between:

1. the physical state $T(t)$ described by the differential equations;
2. the finite set of RK4 states stored every 0.1 s; and
3. the sensor observations recorded every 1.0 s.

Which one is continuous in the mathematical model? Which two are discrete
collections stored by the software?

**My explanation:**

### Exercise 2: Explain hidden truth

Synthetic data generation has access to the full RK4 trajectory, but future
inverse inference should receive only the observation dataset.

1. Why is the dense trajectory called hidden truth?
2. What information leakage would occur if an inverse algorithm used every
   hidden RK4 state as a measurement?
3. Why may tests compare observations with hidden truth?
4. Why should the high-level virtual test-stand function return observations
   rather than bundling dense truth into the same dataset?

**My explanation:**

### Exercise 3: Identify modeling assumptions

For each baseline choice, classify it as a physics-model assumption, numerical
choice, sensor-placement choice, sampling choice, or idealization:

- four uniform thermal nodes;
- 0.1 s RK4 step;
- 1.0 s measurement interval;
- one sensor at every node;
- exact temperature response;
- no lag;
- kelvin as the temperature unit; and
- current recorded with every observation.

**My classification:**

### Exercise 4: State what is not yet realistic

List at least five differences between this ideal dataset and measurements
from a physical thermoelectric test stand. For each difference, state whether
it changes the underlying thermal physics, the observation model, or both.

**My list:**

### Checkpoint 1

Ask Codex to review Exercises 1–4 before studying the schema.

---

## Block 2 — Sensor and dataset schema

### Exercise 5: Name the sensor locations

The allowed locations are:

~~~text
cold_face
hot_face
cold_exchanger
hot_exchanger
~~~

For each location:

1. identify its corresponding temperature in the four-node equations;
2. identify the adjacent thermal elements;
3. state whether it belongs to the TE face or heat exchanger; and
4. state one possible physical sensor-placement challenge.

**My location map:**

### Exercise 6: Distinguish sensor name from location

A sensor has both a unique name and a physical model location.

1. Why are these not the same concept?
2. Could two physical sensors share one location in a future experiment?
3. Why must their names still be unique?
4. Which field should inference use to understand what state is measured?
5. Which field should logging and calibration records use to identify the
   physical instrument?

**My explanation:**

### Exercise 7: Describe one long-form observation

Each ideal observation stores:

~~~text
time
sensor_name
location
temperature
current
~~~

For every field, state:

1. its type;
2. its unit, if any;
3. whether it is an input, measurement, or label; and
4. why it is required.

**My field table:**

### Exercise 8: Long versus wide datasets

Compare the implemented long form—one sensor reading per record—with a wide
table containing one row per time and four temperature columns.

1. Which repeats time and current?
2. Which makes it easier to add or remove sensors?
3. Which handles missing individual readings more naturally?
4. Which may be more convenient for a four-output numerical calculation?
5. Explain why schema choice does not change the physical equations.

**My comparison:**

### Exercise 9: Unit metadata

The dataset explicitly states time in seconds, temperature in kelvin, and
current in amperes.

1. Why are field names alone insufficient for units?
2. What error would occur if Celsius values were passed to Peltier terms that
   require absolute temperature?
3. Why should unit conversion happen at a defined boundary rather than inside
   arbitrary training code?

**My unit analysis:**

### Checkpoint 2

Ask Codex to review Exercises 5–9 before calculating sample counts.

---

## Block 3 — Sampling schedule

### Exercise 10: Count measurement times

For observations every 1.0 s from 0 through 60 s:

1. calculate the number of intervals;
2. calculate the number of measurement times;
3. explain why these numbers differ by one; and
4. state the first, second, next-to-last, and last measurement times.

**My calculation:**

### Exercise 11: Count observation records

The long-form dataset has four sensor readings at every measurement time.

1. Predict the total number of observation records.
2. State the ordering used by the implementation: time-major or sensor-major.
3. Give the sensor sequence for the first time.
4. Find the record index of the first sensor at 1 s.

**My calculation:**

### Exercise 12: Keep solver and sensor intervals separate

Explain why the following values represent different concepts:

~~~text
RK4 time step = 0.1 s
sensor sampling interval = 1.0 s
~~~

Then answer:

1. Does changing the measurement interval change the RK4 physics trajectory?
2. Does changing the RK4 step necessarily change requested measurement times?
3. What may happen to numerical accuracy if the RK4 step becomes too large?
4. What information is lost when the measurement interval becomes larger?

**My explanation:**

### Exercise 13: Handle a non-divisible duration

Suppose duration is 2.5 s and the regular interval is 1.0 s. The implemented
schedule includes the exact final time even though the last interval is only
0.5 s.

1. Write the complete measurement-time tuple.
2. Explain the advantage of including the final experimental state.
3. Explain why the final short interval must be documented.
4. Would every real data logger behave this way automatically?

**My prediction:**

### Exercise 14: Validate a sampling interval

Explain why the interval must be finite and positive. Predict what would go
wrong for zero, a negative number, infinity, or NaN.

**My explanation:**

---

## Block 4 — Sampling and interpolation

### Exercise 15: Exact aligned sample

In the baseline, every 1.0 s measurement time is also an RK4 storage time.

1. Which trajectory value should the ideal sensor return?
2. Why is interpolation unnecessary at those exact times?
3. How should floating-point comparisons be handled near a stored time?

**My explanation:**

### Exercise 16: Linear interpolation by hand

Suppose one temperature history contains:

| Time | Temperature |
| ---: | ---: |
| 0.0 s | 300 K |
| 1.0 s | 296 K |

Calculate the linearly interpolated temperatures at 0.25, 0.5, and 0.75 s.
State the units of the interpolation fraction and temperature result.

**My calculations:**

### Exercise 17: Explain what interpolation assumes

1. Does linear interpolation reproduce the exact nonlinear ODE solution
   between RK4 states?
2. Why is it reasonable when the truth step is sufficiently small?
3. How could step-size refinement test interpolation accuracy?
4. Why should the sampler reject requested times outside the trajectory?

**My explanation:**

### Exercise 18: Map location to a history

Read the location-to-history mapping in `virtual_test_stand.py`.

For every sensor location, identify the selected trajectory field. Explain the
consequence of accidentally mapping `cold_face` to `cold_exchanger`.

Which test would detect that error at the final reference time?

**My code map:**

### Checkpoint 3

Ask Codex to review Exercises 15–18 before studying current alignment.

---

## Block 5 — Current as an observed input

### Exercise 19: Why record current?

1. Is current a predicted state or commanded experimental input?
2. Why must an inverse model know the input applied when a temperature was
   observed?
3. Could the commanded current differ from measured current in hardware?
4. Which distinction will a more realistic test stand eventually need?

**My explanation:**

### Exercise 20: Right-continuous switching

ThermoTwin current schedules are right-continuous. For a step from 0 A to 2 A
at 5 s, state the current at:

- 4.999 s;
- exactly 5.000 s; and
- 5.001 s.

Why must the sampler use the same convention as the integrator?

**My answers:**

### Exercise 21: Temperature continuity versus current jumps

At an ideal instantaneous current switch:

1. may current jump?
2. may Peltier and Joule heat rates jump?
3. may temperature derivatives jump?
4. may a finite-capacitance node temperature jump?
5. what should a sensor record exactly at the switch under the current
   convention?

**My explanation:**

---

## Block 6 — Run and inspect the ideal baseline

### Exercise 22: Predict the returned dataset

Before running the high-level reference function, predict:

1. the number of measurement times;
2. the number of observations;
3. the four initial temperatures;
4. the current in every record;
5. whether the dense 601-point trajectory is stored in the dataset; and
6. whether any value is missing.

**My prediction:**

### Exercise 23: Run a compact inspection

From the repository root, run:

~~~python
from thermotwin import run_ideal_contact_reference_test_stand

dataset = run_ideal_contact_reference_test_stand()

print(len(dataset.measurement_times))
print(len(dataset.observations))
print(dataset.observations[:4])
print(dataset.observations[-4:])
~~~

Compare every output with Exercise 22. For the last four observations, compare
their temperatures with the frozen contact-reference final temperatures.

**My results:**

### Exercise 24: Filter one sensor

Use `dataset.observations_for("cold_face_sensor")`.

1. Predict the returned record count.
2. Verify that names and locations are constant.
3. Verify that times are strictly increasing.
4. Describe the temperature trend physically.
5. Try an unknown sensor name and explain why rejection is safer than an empty
   result.

**My result and interpretation:**

### Exercise 25: Compare sensor and truth resolution

Run the physical reference separately and compare:

- the trajectory time count;
- the dataset measurement-time count; and
- the long-form observation count.

Explain why the largest count is not automatically the most informative
scientific dataset.

**My comparison:**

---

## Block 7 — Read the validation tests

### Exercise 26: Map claims to tests

Find the exact test supporting each claim:

| Claim | Test name |
| --- | --- |
| Sensor names must be nonempty |  |
| Sensor names must be unique |  |
| Sampling intervals must be positive |  |
| The final time is included |  |
| Linear interpolation gives the expected temperature |  |
| All four locations map to the correct histories |  |
| Current is right-continuous at a switch |  |
| The baseline has the predicted counts |  |
| Initial observations are 300 K |  |
| Final observations match hidden reference truth |  |
| Hidden dense truth is not a dataset field |  |

**My test map:**

### Exercise 27: Malformed trajectory checks

Explain why the sampler rejects:

1. empty trajectories;
2. unequal history lengths;
3. non-finite values;
4. times that do not strictly increase; and
5. a requested duration beyond the available trajectory.

For each case, describe one silent scientific error that could occur without
validation.

**My analysis:**

### Exercise 28: Run the focused tests

Run:

~~~bash
python3 -m unittest tests.test_virtual_test_stand
~~~

Record the result. Choose one test about physics meaning and one about software
schema, then explain what each protects.

**My test result:**

---

## Block 8 — Explore and design observation-model extensions

The ideal sampler already supports different measurement intervals. Use that
feature to explore downsampling. Do not implement noise, bias, lag, or missing
data until the ideal baseline is understood and reviewed.

### Exercise 29: Downsampling

Compare 0.5, 1, 2, 5, and 10 s measurement intervals.

1. Predict each measurement-time count for a 60 s experiment.
2. Which transient features become easier to miss?
3. Does downsampling create measurement noise?
4. How might it change parameter identifiability?

**My predictions:**

### Exercise 30: Additive noise

Propose a zero-mean temperature-noise model.

1. State its distribution and standard deviation in kelvin.
2. Should each sensor use the same noise level?
3. Why must synthetic noise use a saved random seed?
4. Which statistics over repeated trials would you report?

**My proposed model:**

### Exercise 31: Sensor bias

Explain the difference between zero-mean random noise and a constant sensor
bias. Predict why repeated samples can average down one but not the other.

How could a calibration measurement help distinguish bias from a model
parameter error?

**My explanation:**

### Exercise 32: Sensor lag

Describe a first-order lag model in words or with an equation. Explain why a
lagged sensor value is not simply the true node temperature plus independent
noise.

Which experiment would help reveal lag most strongly: steady current or a
sharp current pulse? Why?

**My explanation:**

### Exercise 33: Missing observations

Compare:

1. deleting missing records;
2. preserving records with an explicit missing-value mask; and
3. filling missing values by interpolation.

Which approach preserves the fact that no measurement occurred? Which may
silently invent data?

**My comparison:**

### Exercise 34: Restricted sensor sets

Compare these synthetic experiments:

- all four temperatures observed;
- exchanger temperatures only;
- cold-side temperatures only; and
- one exchanger temperature only.

Predict how each affects the ability to infer cold contact resistance. State
which other parameters are assumed known.

**My predictions:**

### Checkpoint 4

Ask Codex to review Exercises 29–34 before adding measurement imperfections.

---

## Interview teach-back

### 30-second explanation

Why does ThermoTwin need an observation model when it already has an RK4
solver?

**My answer:**

### Two-minute explanation

Explain the complete path from four-node physics to dense truth, requested
measurement times, interpolation, sensor-location mapping, long-form records,
and current alignment. State what is idealized and what remains hidden from
future inference.

**My answer:**

### Challenge questions

1. Why are solver resolution and sensor resolution independent?
2. Why does exact synthetic measurement not mean exact hardware measurement?
3. Why include sensor location when the sensor already has a name?
4. Why record the current beside every temperature observation?
5. What does interpolation add, and what error can it introduce?
6. Why begin with all four sensors before studying restricted observability?
7. Which observation imperfection should be added next, and why?

**My answers:**

---

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

| Original claim or calculation | Exact error | Consequence | Corrected reasoning |
| --- | --- | --- | --- |
|  |  |  |  |
