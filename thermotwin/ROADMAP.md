# ThermoTwin project roadmap

This is the governing development roadmap for ThermoTwin. It replaces the
original draft roadmap while preserving its scientific purpose: build a
physics-informed digital twin that can recover hidden thermoelectric-system
parameters from sparse measurements, state when those parameters are not
identifiable, compare control strategies, and recommend informative
experiments.

The revisions reflect what the project has taught us. ThermoTwin is now an
explicitly modular two-node/four-node package, the forward PINNs are
per-experiment physics solvers rather than operating-condition surrogates, and
the most useful demonstration of physics-informed learning is inverse recovery
under sparse or incomplete observation—not merely fitting a temperature
curve.

## Status language

- **Complete:** every current exit criterion is implemented, tested, and
  documented.
- **Partial:** useful validated work exists, but at least one current exit
  criterion remains.
- **Not started:** supporting pieces may exist, but the milestone's scientific
  claim has not been demonstrated.
- **Optional:** valuable after the simulation project, but not required for the
  software MVP.

Passing unit tests establishes software behavior; it does not by itself prove
that a physical assumption matches hardware. Synthetic validation and hardware
validation are reported separately.

## Scope and modeling principles

ThermoTwin models a generic thermoelectric heat pump using public physics. It
does not reproduce proprietary MIMiC hardware.

The project follows these rules:

1. Keep conventional solvers as the numerical reference.
2. Use PINNs where physical constraints help with hidden states, sparse data,
   or parameter inference—not merely because a neural network can be used.
3. Preserve exact sign conventions, units, limiting cases, and energy checks.
4. Split complete operating regimes rather than random time rows.
5. Separate synthetic truth, sensor observations, and inferred quantities.
6. Report failure, bias, and non-identifiability rather than selecting only
   successful runs.
7. Keep standard workloads CPU-first for an M1 MacBook Pro with 16 GB memory;
   Apple MPS remains optional.

## Model hierarchy

The package deliberately retains two compatible physical topologies:

1. The **two-node model** combines each thermoelectric face and its attached
   thermal mass. It is the smallest model for sign, energy, integration, and
   first-PINN checks.
2. The **four-node contact model** separates cold face, hot face, cold
   exchanger, and hot exchanger. It is the main model for contact-resistance
   inference and virtual experiments.

Zero explicit contact resistance is represented by selecting the reduced
two-node topology, not by inserting a zero denominator into the four-node
equations.

---

## Milestone 0 — Scientific specification

**Status: Complete for the current generic single-block scope.**

### Goal

Define the modeled system, sign conventions, equations, known quantities,
unknown quantities, operating regimes, and success metrics before training a
network.

### Required work

- Define positive current and every heat-flow direction.
- Define the meanings and units of $Q_c$, $Q_h$, voltage, power, COP,
  temperature, conductance, resistance, and capacitance.
- Select generic two-node and four-node parameter sets.
- State every energy balance and modeling assumption.
- Separate known parameters from candidates for inference.
- Freeze representative constant-current, unipolar-pulse,
  lower-amplitude-pulse, and bipolar regimes.
- Define numerical, physical, inference, and transfer metrics.

### Exit criteria

- Every state and parameter is defined with a unit.
- Heating/cooling signs and COP definitions are unambiguous.
- The equations use no proprietary information.
- The selected synthetic baselines are explicitly labeled as generic rather
  than hardware-calibrated.

---

## Milestone 1 — Conventional reference physics

**Status: Complete for the implemented two-node and four-node models.**

### Goal

Provide trustworthy numerical reference solutions before asking a neural
network to solve or infer anything.

### Required work

- Implement Peltier heat, Joule heat, conductive leakage, voltage, and power.
- Implement two-node transient balances.
- Implement the modular four-node contact topology.
- Integrate with fixed-step RK4 while splitting steps at current transitions.
- Support constant, step, unipolar pulse, and bipolar current schedules.
- Calculate heat histories, contact drops, COP, and whole-system energy
  closure.
- Check units, signs, current reversal, zero current, steady state, time-step
  convergence, and algebraic energy identities.
- Generate reproducible reference reports.

### Exit criteria

- Temperatures remain finite and physically interpretable in frozen cases.
- Current reversal changes Peltier heat with the correct sign while Joule heat
  remains nonnegative.
- Energy closure satisfies the documented tolerance.
- Reducing the RK4 step produces convergent trajectories.

---

## Milestone 2 — Reproducible virtual test stand

**Status: Complete.**

### Goal

Create controlled synthetic sensor datasets that behave like measurements
without confusing observations with the dense numerical truth.

### Revised requirements

- Generate every regime with the conventional reference solver.
- Attach named sensors to explicit physical nodes.
- Sample observations independently of the integration time step.
- Support configurable Gaussian noise, fixed calibration bias, first-order
  sensor lag, and controlled missing-observation patterns.
- Preserve whole-regime train/validation/test separation.
- Record complete experiment provenance with each generated dataset:
  physical parameter truth, initial and reservoir temperatures, external heat
  inputs, integration step, duration, current schedule, regime name, and split.
- Record the ordered measurement-processing history, including random seeds
  and all applied sensor settings.
- Provide a compact automated quality summary covering schema, counts,
  completeness, ranges, provenance, ground-truth availability, and split
  integrity.

### Intentional changes from the original roadmap

- **Controlled missingness replaces mandatory random deletion.** Missing data
  around a current transition is more informative scientifically than
  arbitrary deletion. Random deletion can still be added as a future study.
- **A small designed regime suite replaces a broad parameter-space sampler.**
  The current training, validation, and bipolar test regimes are interpretable
  and sufficient for the single-parameter experiments. General candidate
  generation moves to experiment selection in Milestone 6B.
- **In-memory immutable datasets are acceptable.** Standardized disk export is
  required only when external tools, large batches, or a published dataset
  need it.
- **Dataset quality is an automated summary, not a separate large report.**

### Deliverables

- Ideal virtual test stand and immutable long-form observation schema.
- Noise, bias, lag, sampling, missingness, and restricted-sensor transforms.
- Complete dataset provenance and reproducible ground-truth configuration.
- Whole-regime training, validation, and test datasets.
- `python3 -m thermotwin.dataset_quality` quality audit.
- Unit and limiting-case tests for every observation transformation.

### Exit criteria

- Frozen datasets regenerate deterministically from their experiment and
  measurement configurations.
- Random transformations record their seeds.
- Validation and test regimes are not time-row fragments of training runs.
- Ground-truth physical parameters remain available for evaluation but dense
  RK4 trajectories are not exposed as observation columns.
- The quality audit passes provenance, truth, and split-integrity checks.

---

## Milestone 3 — Forward physics-informed models

**Status: Partial. The core forward PINNs are validated; the comparison claim
is not finished.**

### Goal

Show that neural temperature functions can satisfy the transient equations and
match conventional reference solutions, then demonstrate where physics helps
relative to an observation-only model.

### Required work

- Scale time, temperature outputs, and residual terms appropriately.
- Use automatic differentiation for temperature rates.
- Evaluate each node balance separately.
- Enforce initial temperatures exactly or verify an equivalent constraint.
- Validate the two-node constant-current PINN.
- Validate the four-node contact PINN.
- Validate piecewise subnetworks for known switched-current schedules while
  maintaining continuous temperatures and one-sided dynamics.
- Compare predictions, errors, residuals, and training histories against RK4.
- Add an explicit whole-system energy-closure diagnostic for PINN predictions.
- Build a matched observation-only baseline for a sparse/missing-data
  reconstruction problem and compare it fairly with the physics-informed
  model.

### Requirements removed or reinterpreted

- The physics-only forward PINN does **not** need a supervised temperature-data
  loss. Observation loss belongs in hybrid or inverse models.
- A second energy equation need not be added to the loss when it merely repeats
  the node balances. Energy closure must instead be calculated and reported as
  an independent diagnostic.
- One universal condition-aware surrogate is not required. The current PINNs
  take time as input and solve a specified experiment. A parametric surrogate
  taking current/conditions as inputs is a later optional acceleration project.
- A time-only network is not expected to generalize to an unseen current
  schedule. Generalization is tested by transferring inferred physical
  parameters through the trusted solver to withheld regimes.

### Completed pieces

- Two-node, contact-aware, and switched-current forward PINNs.
- Exact initial conditions and exact switch-temperature continuity.
- Automatic differentiation and separate residual histories.
- RK4-withheld same-experiment validation and report figures.

### Remaining pieces

- Independent whole-system energy-closure history for PINN trajectories.
- Matched data-only baseline under sparse or missing observations.
- A written comparison explaining when physics helps, when it does not, and
  the fairness limitations of the comparison.

### Exit criteria

- Frozen forward cases meet documented temperature-error thresholds.
- Node residuals and independent energy closure remain below documented
  thresholds.
- Exact initial and segment-interface constraints are verified.
- The data-only comparison uses the same visible observations and comparable
  model capacity/training budget.
- The project can state a defensible advantage or limitation rather than merely
  asserting that PINNs are better.

---

## Milestone 4 — Inverse physical-parameter estimation

**Status: Partial. Ideal single-parameter recovery is strong; imperfect-data
PINN recovery remains.**

### Goal

Recover hidden device-level parameters from sparse observations and validate
the recovered physics on operating regimes excluded from fitting.

### Revised requirements

- Begin with one positive parameter: cold contact resistance.
- Infer it with both a conventional optimizer and an inverse PINN using the
  same observations and bounds.
- Validate hidden hot-side trajectories separately from observed cold-side
  histories.
- Transfer each estimate through the conventional solver to withheld
  validation and bipolar test regimes.
- Repeat inverse-PINN recovery for selected noise, bias, lag, missing-data, and
  restricted-sensor cases.
- Compare point estimates, trajectory errors, transfer errors, runtime, and
  failure modes.
- Document model mismatch explicitly when the inverse model does not include a
  measurement imperfection present in the data.

### Scope change

Jointly releasing a second parameter is no longer required merely to finish
Milestone 4. It belongs in Milestone 5, where correlation and identifiability
can be measured rather than obscured.

### Completed pieces

- Reduced-model inverse thermal-conductance PINN.
- Ideal constant-current and switched-current cold-contact inverse PINNs.
- Positivity constraints, sparse observation losses, conventional scalar
  comparison, hidden-state checks, and transfer to two unseen current regimes.
- Conventional robustness studies for all implemented measurement effects.

### Remaining pieces

- Inverse PINN on selected imperfect datasets, starting with missing readings.
- Direct imperfect-data comparison with the conventional estimator.
- Failure/recovery criteria across several neural seeds.

### Exit criteria

- Ideal recovery is accurate from more than one plausible initial guess.
- At least one noisy and one structured-missingness case are evaluated.
- Recovered parameters predict withheld regimes.
- Conventional and PINN methods receive identical visible observations.
- Failures and sensitivity to initialization are reported.

---

## Milestone 5 — Identifiability and uncertainty

**Status: Partial. Conventional single-parameter robustness is implemented;
joint identifiability and calibrated uncertainty are not.**

### Goal

Determine which parameter combinations can be recovered, with which sensors
and excitations, and with what uncertainty.

### Revised requirements

- Use sensitivity profiles or local information measures before expensive PINN
  ensembles.
- Vary sensor location/count, sampling interval, noise, lag, bias, missingness,
  and current excitation.
- Jointly release a scientifically motivated second parameter, likely cold
  contact resistance with one capacitance or effective reservoir conductance.
- Calculate parameter correlations and profile the loss surface.
- Use multi-start fitting and selected bootstrap/ensemble cases.
- Construct uncertainty intervals and check their coverage against synthetic
  truth.
- Identify cases where the data cannot separate contact dynamics, sensor lag,
  and thermal capacitance.

### Scope change

Large PINN ensembles are not required for every grid point. Conventional
sensitivities and optimizers can map the space cheaply; PINN ensembles should
be reserved for representative cases where they add evidence.

### Existing foundation

- Repeated Gaussian-noise trials.
- Isolated bias, lag, turn-off missingness, sensor-restriction, and combined
  imperfection studies.
- A local turn-off information metric.

### Exit criteria

- At least one identifiable and one underdetermined multi-parameter case are
  demonstrated.
- Correlations and failure regions are visible rather than inferred from one
  fit.
- Reported intervals have tested synthetic-truth coverage.
- Conclusions use repeated trials or multi-start fits.

---

## Milestone 6A — Control comparison

**Status: Not started. Current schedules and COP diagnostics are ready.**

### Goal

Compare continuous and pulsed operation objectively using the validated
physics model.

### Required work

- Define cooling/heating capacity, module COP, delivered COP, temperature
  constraints, current limits, and comparison horizon.
- Establish fair continuous-current baselines.
- Sweep pulse amplitude, duty cycle, and period.
- Compare equal electrical energy and equal delivered heat where appropriate.
- Produce COP-versus-capacity Pareto fronts and operating maps.
- Propagate representative parameter uncertainty through the comparison.

### Scope change

The conventional solver—not a PINN—is the default control-sweep engine because
it is fast and already validated. A neural surrogate is justified only if the
candidate count makes the conventional solver a demonstrated bottleneck.

### Exit criteria

- Comparisons use explicit fair constraints.
- Safety and temperature limits are enforced.
- Pulsed operation is allowed to win, lose, or tie according to the results.
- Conclusions remain stable across selected parameter uncertainty.

---

## Milestone 6B — Next-experiment selection

**Status: Not started.**

### Goal

Recommend the next feasible experiment that is expected to reduce uncertainty
or separate correlated parameters.

### Required work

- Generate candidate current amplitudes, pulse timings, sampling intervals,
  and sensor configurations.
- Apply physical, duration, and safety constraints.
- Rank candidates using parameter sensitivity, expected information, or
  ensemble disagreement.
- Simulate the top recommendation with hidden truth.
- Refit the model using the added experiment.
- Measure the actual reduction in parameter error/correlation/interval width.
- Compare the recommended experiment with at least one naive choice.

Flow rate is not yet an independent input in the lumped model. It should enter
the candidate space only after a documented flow-to-heat-transfer model or
hardware data is added; until then, reservoir conductance is the effective
heat-transfer parameter.

### Exit criteria

- Candidate ranking is reproducible.
- The recommendation is feasible under stated constraints.
- The selected experiment improves a predeclared uncertainty metric in
  simulation.
- Improvement is measured against a baseline selection strategy.

---

## Milestone 7 — Interview-ready research artifact

**Status: Partial and developed continuously.**

### Goal

Make the scientific result reproducible, understandable, and useful in an
interview without requiring the viewer to inspect the entire source tree.

### Required work

- Maintain concise and detailed READMEs, this roadmap, equations, assumptions,
  limitations, and learning notes.
- Keep automated unit, physics, regression, and report tests.
- Add a continuous-integration workflow for the CPU test suite.
- Maintain a one-command showcase and automatically generated figures.
- Create a final technical summary centered on engineering conclusions.
- Document negative, biased, and non-identifiable cases.
- Prepare a five-slide interview deck, 90-second demonstration, and concise
  resume bullets.

### Scope change

An interactive application is optional rather than mandatory. The existing
one-command static showcase can satisfy the MVP if it communicates the evidence
more clearly and reproducibly than a hurried interface.

### Existing foundation

- Modular package, extensive tests, two levels of README documentation,
  experiment walkthroughs, learning worksheets, report commands, and a focused
  PINN showcase.

### Exit criteria

- A clean installation can reproduce principal numbers and figures.
- Continuous integration passes on the public repository.
- The main README communicates the project in roughly two minutes.
- The detailed report makes assumptions and limitations easy to locate.
- The presentation distinguishes synthetic validation from hardware evidence.

---

## Milestone 8 — Optional hardware validation

**Status: Optional; not started.**

### Goal

Measure the synthetic-to-real gap with a safe benchtop Peltier experiment.

### Required work

- Define current, voltage, temperature, condensation, and handling limits.
- Calibrate temperature, current, and voltage sensors.
- Record ambient conditions and sensor placement.
- Collect constant-current and pulse experiments.
- Fit parameters using a subset of experiments.
- Predict an experiment withheld in its entirety.
- Compare inferred values with datasheet or independent estimates where those
  comparisons are physically meaningful.
- Document unmodeled losses and model discrepancy.

### Exit criteria

- Safety constraints and calibration procedures are documented.
- Raw data and processing provenance are retained.
- At least one genuinely withheld experiment is predicted.
- Disagreement is analyzed rather than hidden by refitting every case.

## Recommended execution order from the current state

1. Finish Milestone 3 with PINN energy closure and a matched data-only
   sparse/missing-data comparison.
2. Finish Milestone 4 by training the inverse PINN on selected imperfect
   datasets and comparing it fairly with the conventional estimator.
3. Complete Milestone 5's two-parameter identifiability and uncertainty study.
4. Run Milestone 6A's continuous-versus-pulsed control study.
5. Use its feasible candidate space for Milestone 6B experiment selection.
6. Finalize Milestone 7 deliverables throughout, rather than postponing all
   documentation until the end.
7. Attempt Milestone 8 only if safe hardware and sufficient time are available.

## Final project claim

The intended final result is not simply that a PINN predicts temperature. It
is that ThermoTwin:

- enforces a transparent thermoelectric energy model;
- estimates hidden interface behavior from sparse, imperfect measurements;
- identifies when the measurements cannot support a unique conclusion;
- validates recovered physics on unseen current regimes;
- compares control schedules under explicit engineering objectives; and
- recommends the next experiment expected to reduce uncertainty.

That claim is complete only when each supporting result has a reproducible
configuration, conventional baseline, quantitative metric, and documented
limitation.
