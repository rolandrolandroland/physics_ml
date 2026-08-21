# ThermoTwin learning notes

These notes are for explaining the model in my own words and checking that I
understand every physical assumption, equation, sign, unit, and implementation
choice. They are intentionally separate from the package README.

## Note index

| Note | Purpose | Status      |
| --- | --- |-------------|
| [01 — Sign conventions](01_sign_conventions.md) | Define heat-flow, current, voltage, and temperature signs | Revising    |
| [02 — Thermoelectric terms](02_thermoelectric_terms.md) | Explain the Peltier, Joule, and conductive contributions | Not started |
| [03 — Energy balances](03_energy_balances.md) | Derive the cold, hot, and combined-node balances | Not started |
| [04 — Transient RHS](04_transient_rhs.md) | Map the balances to the implemented temperature rates | Not started |
| [05 — Forward experiments](05_forward_experiments.md) | Record predictions, simulation designs, and interpretations | Not started |
| [06 — Time integrator](06_time_integrator.md) | Understand transient physics, RK4, trajectory code, and numerical checks | Not started |
| [07 — Time-varying current](07_time_varying_current.md) | Understand current schedules, switching physics, discontinuities, and pulse tests | Not started |
| [08 — Forward PINN](08_forward_pinn.md) | Understand the forward PINN physics, code, training loss, and RK4 validation | Not started |
| [09 — Inverse thermal conductance](09_inverse_thermal_conductance.md) | Understand sparse observations, trainable $K$, inverse losses, identifiability, and validation | Not started |
| [10 — Contact-aware transient](10_contact_aware_transient.md) | Understand modular topology, contact heat signs, four-node balances, RK4, and limiting cases | Not started |
| [11 — Contact reference and diagnostics](11_contact_reference_diagnostics.md) | Understand the frozen contact experiment, derived histories, energy closure, COP definitions, topology comparison, and resistance sweep | Not started |
| [12 — Virtual test stand](12_virtual_test_stand.md) | Understand sensor locations, observation schemas, sampling, interpolation, hidden truth, noise, bias, lag, missing readings, provenance, and quality checks | Not started |
| [13 — Measurement imperfections](13_measurement_imperfections.md) | Consolidate temperature noise, sensor bias, sensor lag, deterministic missingness, transformation order, and identifiability | Not started |
| [14 — Contact-resistance experiment](14_contact_resistance_experiment.md) | Understand pulse design, scalar inference, held-out regimes, repeated noise, fixed bias, sensor lag, informative missingness, restricted sensor sets, combined imperfections, empirical statistics, and limitations | Not started |
| [15 — Contact-aware forward PINN](15_contact_forward_pinn.md) | Understand four learned temperatures, four contact energy residuals, exact initial conditions, autograd, loss construction, RK4 validation, and the bridge to inverse contact inference | Not started |
| [16 — Inverse contact-resistance PINN](16_inverse_contact_resistance_pinn.md) | Understand positive resistance parameterization, sparse cold-pair observations, joint physics/data loss, identifiability, conventional comparison, and parameter transfer to unseen pulses | Not started |
| [17 — Piecewise contact forward PINN](17_piecewise_contact_forward_pinn.md) | Understand switched-current physics, continuous temperatures, discontinuous rates, domain decomposition, exact interface chaining, collocation, routing, and RK4 validation | Not started |
| [18 — Piecewise inverse contact resistance](18_piecewise_inverse_contact_resistance.md) | Understand shared positive resistance inference from a pulse, joint physics/data loss, loss weighting, identical-data comparison, switch continuity, identifiability, and parameter transfer | Not started |
| [19 — COP operating maps](19_cop_operating_map.md) | Understand cooling/heating COP, current and lift sweeps, contact penalties, algebraic steady state, useful-capacity thresholds, and fair equal-load comparisons | Not started |
| [20 — Pulse operating envelope](20_pulse_operating_envelope.md) | Understand how seconds-scale transient pulses connect to the steady COP map, fair objectives, mean/RMS current, storage drift, and negative control results | Not started |
| [21 — PWM power electronics](21_pwm_power_electronics.md) | Understand direct versus smoothed PWM current, first and second current moments, averaged thermoelectric heat, converter loss, wall COP, code, tests, and next electrical extensions | Not started |

Suggested statuses are `Not started`, `Draft`, `Revising`, and `Reviewed`.

## Learning workflow

1. Write the explanation and predictions without copying the README or code.
2. Work through at least one limiting case and one numerical example by hand.
3. Identify the exact code function and test corresponding to each claim.
4. Ask Codex to review the physics, signs, units, and interpretation.
5. Revise conceptual errors before asking Codex to polish wording.
6. Record important mistakes and their consequences in the corrections section.
7. Change the note status to `Reviewed` only after the reasoning and tests agree.

## Questions that span multiple notes

> Record questions here when they do not belong to only one topic.

## Vocabulary to revisit

| Term | My current explanation | What remains unclear |
| --- | --- | --- |
|  |  |  |
