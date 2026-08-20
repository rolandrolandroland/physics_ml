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
- `thermotwin/measurement_noise.py`: reproducible Gaussian temperature noise;
- `thermotwin/measurement_bias.py`: fixed per-sensor temperature offsets;
- `thermotwin/measurement_lag.py`: first-order dynamic sensor response;
- `thermotwin/measurement_missingness.py`: deterministic sensor outages;
- `thermotwin/dataset_metadata.py`: reproducible experiment truth and ordered
  observation-processing provenance;
- `thermotwin/dataset_quality.py`: completeness, range, truth, provenance, and
  whole-regime split checks;
- `tests/test_virtual_test_stand.py`: schema, timing, interpolation, current,
  and validation checks;
- `tests/test_measurement_noise.py`: determinism, zero-noise, per-sensor, and
  sample-statistics checks;
- `tests/test_measurement_bias.py`: zero-bias, persistence, isolation, and
  composition checks;
- `tests/test_measurement_lag.py`: time constants, dynamics, ordering, and
  limiting-case checks;
- `tests/test_measurement_missingness.py`: outage boundaries, record counts,
  schema, ordering, and limiting-case checks; and
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

The ideal sampler already supports different measurement intervals, and the
independent Gaussian temperature-noise, fixed-bias, first-order sensor-lag,
and deterministic missing-observation layers are now implemented. Use these
features to explore downsampling and measurement effects. Note 13 consolidates
the four measurement imperfections and their complete transformation order.

### Exercise 29: Downsampling

Compare 0.5, 1, 2, 5, and 10 s measurement intervals.

1. Predict each measurement-time count for a 60 s experiment.
2. Which transient features become easier to miss?
3. Does downsampling create measurement noise?
4. How might it change parameter identifiability?

**My predictions:**

### Exercise 30: Additive noise

Before reading `measurement_noise.py`, propose a zero-mean temperature-noise
model. Then compare it with the frozen generic baseline: independent Gaussian
errors, 0.05 K standard deviation, and random seed 2026.

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

Ask Codex to review Exercises 29–34 before analyzing the implemented noise
layer.

---

## Block 9 — Trace the implemented Gaussian-noise layer

### Exercise 35: Separate distribution parameters from realized errors

The baseline distribution has mean zero and standard deviation 0.05 K.

1. Must one finite dataset have an error mean of exactly zero?
2. Must its RMS error equal exactly 0.05 K?
3. Why should errors include both signs?
4. What happens to these statistics as the number of independent readings
   becomes very large?

**My explanation:**

### Exercise 36: Verify immutability and schema preservation

Read `apply_gaussian_temperature_noise`.

1. Which field of each observation is replaced?
2. Which fields are copied exactly?
3. Why is returning a new dataset safer than modifying the ideal dataset?
4. Why does `TemperatureNoiseResult` retain the noise configuration?
5. Why does it not retain ideal truth?

**My code trace:**

### Exercise 37: Predict the zero-noise limiting case

Set the default standard deviation to 0 K with no overrides.

1. Predict every returned temperature.
2. Predict whether record counts or metadata change.
3. Explain why this is a limiting-case test rather than a useful noisy
   experiment.
4. Find the exact automated test.

**My prediction and result:**

### Exercise 38: Explain the random seed

Run the transformation twice with seed 2026 and once with a different seed.

1. Which datasets should match exactly?
2. Why is reproducibility essential for debugging and regression tests?
3. Why should uncertainty studies eventually use many different recorded
   seeds?
4. Does fixing a seed make the measurements physically less random?

**My explanation:**

### Exercise 39: Configure one sensor differently

Use zero default noise and a 0.10 K override for `cold_face_sensor`.

1. Predict which records may change.
2. Predict which records must remain exact.
3. Why are override names validated against dataset sensor names?
4. Design a physically motivated case in which different sensors would have
   different uncertainty.

**My prediction and result:**

### Exercise 40: Calculate realized error statistics

Generate the frozen noisy reference and separately generate the ideal dataset.
For the 244 paired readings, calculate:

1. mean temperature error;
2. RMS temperature error;
3. maximum absolute error; and
4. the same statistics for each sensor individually.

Explain why comparing the two datasets is appropriate for synthetic
validation but would not be possible with unknown hardware truth.

**My calculations and interpretation:**

### Checkpoint 5

Ask Codex to review Exercises 35–40 before analyzing fixed bias or implementing
lag.

---

## Block 10 — Trace the implemented fixed-bias layer

### Exercise 41: Distinguish bias from random noise

Compare these observation equations:

$$
T_{\mathrm{noisy}}=T_{\mathrm{ideal}}+\epsilon,
\qquad \epsilon\sim\mathcal N(0,\sigma^2),
$$

$$
T_{\mathrm{biased},s}=T_{\mathrm{ideal},s}+b_s.
$$

1. Which error changes from reading to reading?
2. Which remains constant for one sensor?
3. Which tends to average toward zero under the implemented assumptions?
4. Which could be confused with a persistent model discrepancy?

**My comparison:**

### Exercise 42: Predict the frozen bias-only dataset

The generic baseline assigns +0.10 K to `cold_face_sensor` and 0 K to all
other sensors.

Before running it, predict:

1. the number of times and records;
2. every initial sensor reading;
3. which final reading differs from ideal;
4. the mean cold-face error over 61 readings; and
5. whether current or time changes.

**My predictions and results:**

### Exercise 43: Trace configuration and validation

Read `FixedTemperatureBias` and `apply_fixed_temperature_bias`.

1. Why may a valid bias be positive, negative, or zero?
2. Why must it be finite?
3. Why must override names be unique and known to the dataset?
4. Which observation field is replaced?
5. Which fields remain exact?

**My code trace:**

### Exercise 44: Verify the zero-bias limiting case

Apply a default bias of 0 K with no overrides to both an ideal dataset and a
noisy dataset.

1. Predict both outputs.
2. Why should equality hold exactly rather than statistically?
3. Which automated test checks the ideal case?
4. What additional test would check the noisy-input case?

**My prediction:**

### Exercise 45: Explain composition with noise

For additive independent noise and fixed bias, compare

~~~text
ideal -> noise -> bias
ideal -> bias -> noise
~~~

1. Derive the final temperature expression for each order.
2. Why should they agree mathematically?
3. Why might floating-point results differ in their last bits?
4. Why will sensor lag generally make transformation order important?
5. Why does the combined result retain both configurations?

**My derivation and explanation:**

### Exercise 46: Design a calibration check

Propose a controlled condition with a known uniform temperature that could
help estimate sensor offsets.

1. What reference instrument or condition is required?
2. How many repeated measurements would you take?
3. How would you separate random scatter from fixed offset?
4. What could make the apparent bias temperature-dependent?
5. Why is the current +0.10 K value not a calibration result?

**My design:**

### Checkpoint 6

Ask Codex to review Exercises 41–46 before analyzing sensor lag and the
combined measurement pipeline.

---

## Block 11 — Trace the implemented first-order lag layer

### Exercise 47: Derive the direction of the lagged response

Start from

$$
\tau\frac{dT_m}{dt}=T_{\mathrm{node}}-T_m.
$$

1. Determine the sign of $dT_m/dt$ when the node is warmer than the sensor.
2. Determine it when the node is colder.
3. Explain why $T_m$ approaches rather than instantly equals the node.
4. State the units of every term.
5. Explain the limiting behavior as $\tau$ approaches zero and infinity.

**My derivation:**

### Exercise 48: Calculate one discrete lag step

Use $\tau=2$ s, $\Delta t=1$ s, previous sensor temperature 300 K, and current
node temperature 299 K.

1. Calculate $a=\exp(-\Delta t/\tau)$.
2. Calculate the new reported temperature.
3. Verify that it lies between 299 K and 300 K.
4. Repeat for $\tau=4$ s and explain which sensor responds more slowly.

**My calculations:**

### Exercise 49: Predict the cold-face reference

The cold face cools after current is applied, while its virtual sensor has a
2 s time constant.

Before running the workflow, predict:

1. the initial lag error;
2. the sign of later lag error;
3. whether the error grows indefinitely;
4. what happens as the physical trajectory approaches steady state; and
5. which other sensor readings change.

Record the errors at 1 s, the maximum-error time, and 60 s.

**My predictions and results:**

### Exercise 50: Explain dense filtering before downsampling

Compare:

~~~text
dense truth -> lag -> sample every 5 s
dense truth -> sample every 5 s -> lag
~~~

1. Why can these produce different sensor responses?
2. Which better represents a physical sensor evolving between saved readings?
3. Compare the implemented 1 s and 5 s outputs at common times.
4. Why does the high-level workflow still allow the low-level filter to accept
   irregularly spaced data?

**My explanation:**

### Exercise 51: Trace the complete measurement order

The combined baseline uses

~~~text
truth -> lag -> sampling -> bias -> noise
~~~

1. Why should node truth enter the lag model before random measurement noise?
2. What mistake would result from filtering independent readout noise as if it
   were node temperature?
3. Why do fixed additive bias and additive noise commute mathematically?
4. Why does lag generally not commute with noise?
5. Where is every configuration retained?

**My code trace:**

### Exercise 52: Distinguish sensor lag from sensor thermal loading

The implemented lag changes only the reported temperature.

1. Does it remove heat from the modeled node?
2. Does it add a new physical thermal capacitance to the four-node model?
3. What equations would be required to model a sensor bead and its contact as
   a coupled physical node?
4. When might sensor thermal loading be negligible?
5. Why must hardware validation revisit this assumption?

**My explanation:**

### Exercise 53: Design a time-constant identification experiment

Propose an input that makes sensor lag observable.

1. Would a steady temperature or sharp transient be more informative?
2. Which node and sensor would you monitor?
3. What sampling interval would you choose relative to the expected time
   constant?
4. How could model thermal inertia be confused with sensor lag?
5. What independent reference measurement could help separate them?

**My experiment design:**

### Checkpoint 7

Ask Codex to review Exercises 47–53, then continue with the missing-observation
exercises in `13_measurement_imperfections.md`.

---

## Block 8 — Dataset provenance and quality

### Exercise 54: Separate ground-truth metadata from hidden trajectory truth

The dataset now stores the physical parameter values and complete experiment
configuration, but it still does not store the dense RK4 temperature history.

1. Why are known synthetic parameters required for evaluation?
2. Why would dense hidden temperatures be a different kind of information?
3. Which one may an inference routine use during fitting?
4. Which one should evaluation code use after fitting?
5. Explain why recording ground truth does not itself prove hardware realism.

**My explanation:**

### Exercise 55: Reconstruct an experiment from provenance

Inspect `dataset.provenance.experiment`, then answer:

1. Which three thermoelectric parameters are recorded?
2. Which eight four-node thermal parameters are recorded?
3. How are scalar and piecewise currents distinguished?
4. What do `regime_name` and `split` prevent us from forgetting?
5. What object does `to_experiment()` reconstruct?
6. Confirm that reconstructing the experiment does not reconstruct its solved
   temperature trajectory.

**My code trace:**

### Exercise 56: Interpret the quality report

Run:

~~~bash
python3 -m thermotwin.dataset_quality
~~~

1. Why are there 732 expected records?
2. What does 100 percent completeness establish?
3. Why must regime names be unique across splits?
4. Why does a `PASS` for ground-truth availability not establish
   identifiability?
5. Predict the completeness of the 233-record controlled-outage dataset.
6. Name two hardware-data quality checks that this synthetic audit does not
   yet contain.

**My interpretation:**

### Checkpoint 8

Ask Codex to review Exercises 54–56. Be prepared to explain why reproducible
provenance, data completeness, parameter identifiability, and hardware validity
are four different claims.

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
8. Why can a dataset expose synthetic parameter truth without exposing dense
   temperature truth to the fitting algorithm?

**My answers:**

---

## Open questions

> Record anything that is still unclear.

## Corrections and revisions

| Original claim or calculation | Exact error | Consequence | Corrected reasoning |
| --- | --- | --- | --- |
|  |  |  |  |
