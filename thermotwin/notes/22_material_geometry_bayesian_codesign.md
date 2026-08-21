# Exercise sheet: material, geometry, and Bayesian co-design

Status: Not started

This worksheet teaches both the thermoelectric science and the code behind the
public-data-seeded design campaign. Work in order. Write predictions before
running code, keep units with every numerical answer, and distinguish a
physical conclusion from a consequence of a synthetic assumption.

The main walkthrough is
[`../MATERIAL_GEOMETRY_BAYESIAN_CODESIGN.md`](../MATERIAL_GEOMETRY_BAYESIAN_CODESIGN.md).

## Learning goals

After completing the sheet, I should be able to:

1. explain why $S$, $\sigma$, and $k$ must come from the same material sample;
2. derive module $\alpha$, $R$, and $K$ from p/n leg properties and geometry;
3. predict the competing effects of leg length, area, and couple count;
4. distinguish module COP, wall COP, delivered cooling, and heat flux;
5. explain the initial Latin-hypercube experiment;
6. explain what the Gaussian process predicts and what expected improvement
   chooses;
7. make a fair BO-versus-random comparison;
8. interpret flat optimization curves without calling them failures;
9. explain why a nominally optimal design can be commercially fragile;
10. identify which parts of the campaign are public data, physics, or synthetic
    engineering assumptions.

## Files to keep open

- `thermotwin/material_catalog.py`
- `thermotwin/material_geometry_codesign.py`
- `thermotwin/material_geometry_codesign_report.py`
- `tests/test_material_catalog.py`
- `tests/test_material_geometry_codesign.py`
- `tests/test_material_geometry_codesign_report.py`
- `thermotwin/MATERIAL_GEOMETRY_BAYESIAN_CODESIGN.md`

---

## Part 1: data provenance and scientific honesty

### Exercise 1.1: classify every input

Complete the table without copying the walkthrough.

| Quantity | Public experimental record, physics equation, or synthetic assumption? | Why? |
| --- | --- | --- |
| sample 9107 Seebeck coefficient |  |  |
| $ZT=S^2\sigma T/k$ |  |  |
| $2.0\times10^{-10}$ ohm m2 electrical-interface resistivity |  |  |
| 0.04 W/K package parasitic conductance |  |  |
| 0.95 converter efficiency |  |  |
| 0.10--0.50 K/W contact range |  |  |
| four-node energy balances |  |  |
| relative prototype cost index |  |  |
| 3% Seebeck uncertainty |  |  |

### Exercise 1.2: the Frankenstein-material error

Suppose three different samples have these properties:

| Sample | $S$ (microV/K) | $\sigma$ (kS/m) | $k$ (W/m K) |
| --- | ---: | ---: | ---: |
| A | 240 | 40 | 1.0 |
| B | 170 | 160 | 1.5 |
| C | 130 | 70 | 0.55 |

1. Calculate $ZT$ at 300 K for A, B, and C.
2. Construct the fictitious record made from the largest $|S|$, largest
   $\sigma$, and smallest $k$.
3. Calculate its apparent $ZT$.
4. Explain exactly why the fictitious result is invalid even though every
   individual number was measured somewhere.
5. Find the code rule or test that protects ThermoTwin from cross-row mixing.

### Exercise 1.3: fixed snapshot limitations

Answer in my own words:

1. What does the snapshot DOI identify?
2. What does the MD5 checksum establish, and what does it not establish?
3. Why is a 2019 interpolated snapshot useful for reproducibility but
   insufficient for claiming the latest best material?
4. Why must the original paper be checked before manufacturing from a digitized
   point?

---

## Part 2: derive material-to-module scaling

### Exercise 2.1: one p/n couple

Start from electrical resistance $R=\rho L/A$, electrical resistivity
$\rho=1/\sigma$, and thermal conductance $K=kA/L$.

1. Derive the electrical resistance of one p/n couple, remembering that the
   legs carry current in series.
2. Derive the thermal conductance of one couple, remembering that the legs
   conduct heat in parallel.
3. Explain why the couple Seebeck coefficient is $S_p-S_n$ rather than
   $S_p+S_n$ when $S_n$ is stored as a negative number.
4. Extend all three expressions to $N$ couples.
5. Locate the equivalent calculation in `module_thermoelectric_parameters`.

### Exercise 2.2: numerical module calculation

Use samples 9107 and 10562 with:

- $N=83$;
- $L=1.0791687$ mm;
- $A=0.8454635$ mm2;
- per-interface specific electrical contact resistivity
  $\rho_c=2.0\times10^{-10}$ ohm m2;
- package parasitic conductance 0.04 W/K.

Calculate by hand, showing unit conversions:

1. $\alpha$ in V/K;
2. leg-only electrical resistance in ohms;
3. the resistance of four electrical interfaces per couple using
   $R_{\mathrm{contact}}=4N\rho_c/A$;
4. total electrical resistance;
5. leg-only thermal conductance in W/K;
6. final thermal conductance after the package parasitic.

Then compare with the implemented values. Record the difference and decide
whether it is arithmetic rounding or a code/physics discrepancy.

### Exercise 2.3: limiting-case predictions

Before evaluating any code, fill in each multiplier.

| Change | $\alpha$ multiplier | bulk $R$ multiplier | electrical-contact $R$ multiplier | leg $K$ multiplier | active volume multiplier |
| --- | ---: | ---: | ---: | ---: | ---: |
| double $N$ |  |  |  |  |  |
| double $L$ |  |  |  |  |  |
| double $A$ |  |  |  |  |  |
| double $\sigma_p$ only |  |  |  |  |  |
| halve $k_n$ only |  |  |  |  |  |

Check the first three predictions against `ModuleScalingTests`. Explain why a
fixed 0.04 W/K package leak prevents total $K$ from scaling exactly even when
leg $K$ does. Explain why doubling leg length changes bulk resistance but
leaves an areal interface resistance unchanged.

### Exercise 2.4: why an areal contact term matters

Compare these two models:

$$
R_{\mathrm{old}}=1.05R_{\mathrm{legs}},
\qquad
R_{\mathrm{new}}=R_{\mathrm{legs}}+4N\rho_c/A.
$$

1. For fixed $N$ and $A$, derive the contact fraction as a function of $L$ in
   each model.
2. Which model predicts the same 5% contact fraction at every leg length?
3. Why does that behavior incorrectly favor short legs during geometry
   optimization?
4. Identify the class field that stores $\rho_c$ and the helper that reports
   bulk, contact, and total resistance separately.
5. Explain why the default $\rho_c$ is still an engineering assumption even
   though its order of magnitude is anchored to a published measurement.

### Exercise 2.5: thickness is not a one-direction benefit

Write a short explanation of this statement:

> Shorter legs can increase heat-pumping capacity, but they also increase
> passive thermal leakage.

Your answer must explicitly mention how $R$, $K$, Joule heat, conduction heat,
and current density respond. State one missing spatial/manufacturing effect
that the lumped geometry model cannot resolve.

---

## Part 3: contacts, heat rejection, and electrical drive

### Exercise 3.1: trace one steady evaluation

Read `evaluate_design_current` from top to bottom and make a numbered flowchart
using these phrases exactly once:

- current moments;
- module parameters;
- contact/exchanger parameters;
- reservoir temperatures;
- four-node steady solve;
- module heat rates;
- delivered heat rates;
- converter input power;
- wall COP;
- constraints and utility.

For each step, write the main function or class used in code.

### Exercise 3.2: boundary heat versus module heat

At steady state the code checks

$$
Q_c=G_c(T_{c,\infty}-T_{x,c})
$$

and

$$
Q_h=G_h(T_{x,h}-T_{h,\infty}).
$$

1. Explain why these equalities hold at equilibrium.
2. Explain why they need not be equal instantaneously during a transient.
3. Identify the two runtime checks that would fail if a sign were reversed.
4. Predict how reducing hot exchanger conductance changes hot-face
   temperature, face $\Delta T$, cooling, and COP.

### Exercise 3.3: current moments

For 0.80 A mean current and 10% triangular peak-to-peak ripple:

1. calculate peak current;
2. calculate $\overline{I^2}$;
3. calculate the Joule multiplier over ideal DC;
4. explain why the Peltier term does not use RMS current;
5. locate the helper that constructs these moments.

### Exercise 3.4: module COP versus wall COP

For a hypothetical point with 5 W cooling, 2 W module terminal power, 95%
converter efficiency, and 0.05 W fixed loss:

1. calculate module cooling COP;
2. calculate supply power;
3. calculate wall cooling COP;
4. explain which COP a product investor or customer would usually care about;
5. identify one converter behavior missing from the constant-efficiency model.

---

## Part 4: application-specific objectives

### Exercise 4.1: compare the three utilities

Write the implemented utility equation for each application. Then consider a
feasible operating point with:

- cooling 5 W;
- wall COP 2;
- heat flux 1.4 W/cm2;
- cost index 1.25.

Calculate all three utilities. Explain why their numerical values should not be
compared across applications as though they had the same meaning.

### Exercise 4.2: constraint penalty

Read `_application_utility`.

1. List its four explicit constraint violations.
2. What utility sign marks an infeasible point?
3. Why does the current-density constraint have to be checked separately?
4. What happens if no scanned current is feasible?
5. Suggest one temperature or mechanical constraint that should be added
   before hardware optimization.

### Exercise 4.3: predict operating-point changes

Before reading the campaign result, predict whether the capacity-first current
will be lower than, equal to, or higher than the efficiency-first current for
the same hardware. Justify the prediction using linear Peltier heat and
quadratic Joule heat.

Then inspect the selected 10 K operating points:

| Objective | Mean current | Cooling | Wall COP |
| --- | ---: | ---: | ---: |
| efficiency-first | 0.494 A | 2.524 W | 2.856 |
| capacity-first | 0.805 A | 4.662 W | 2.207 |

Explain whether the result agrees with the prediction.

### Exercise 4.4: identify a binding constraint

The high-lift and capacity-first winners both report 100.00% current-density
utilization. The efficiency-first winner reports 61.30%.

1. Write the formula for peak current density used by the code.
2. Calculate the exact allowed mean current for triangular 10% ripple using
   the unrounded areas of the two selected designs.
3. Why can the printed 2.111 A appear slightly larger than its 2.11059 A cap?
4. Why must a result at 100% utilization be described as a constrained
   boundary solution rather than an unconstrained optimum?
5. Locate the field and threshold used to label a point as binding.

---

## Part 5: the 24-design initial experiment

### Exercise 5.1: Latin hypercube by hand

For four samples in one dimension, divide $[0,1)$ into four equal strata.

1. Write the four intervals.
2. Choose one point in each interval.
3. Shuffle their order.
4. Explain why four purely random points could cluster while the stratified
   points cannot omit an entire quarter of the range.
5. Extend the explanation conceptually to eight dimensions.

### Exercise 5.2: test the sampler

Read `latin_hypercube` and
`test_latin_hypercube_uses_every_stratum_once_per_dimension`.

1. Explain the purpose of shuffling the stratum indices separately for each
   dimension.
2. Explain the purpose of random jitter inside a stratum.
3. State what the fixed seed guarantees.
4. State what it does not guarantee about physical optimality.
5. Why are p/n choices encoded as categorical indices rather than interpolated
   between two materials?

### Exercise 5.3: interpret feasibility counts

The initial feasible counts are 17/24, 16/24, and 16/24.

1. What does “feasible” mean in this code?
2. Does 17/24 prove that 70.8% of all manufacturable designs are feasible?
3. Why or why not?
4. What information about the defined virtual envelope can the count support?

---

## Part 6: Gaussian-process Bayesian optimization

### Exercise 6.1: surrogate inputs

Count the entries returned by `design_features`:

1. How many normalized continuous features are present?
2. How many p-material one-hot features?
3. How many n-material one-hot features?
4. What is the total feature width?
5. Explain why treating sample ID 10562 as a large numerical coordinate would
   be meaningless.

### Exercise 6.2: GP mean and uncertainty

In my own words, explain:

1. what the GP posterior mean represents;
2. what the GP posterior standard deviation represents;
3. why nearby feature vectors have larger kernel covariance;
4. why the diagonal nugget is needed;
5. why the nugget makes the training-point prediction almost, but not exactly,
   interpolating.

Connect the last answer to the $2\times10^{-3}$ tolerance in the GP unit test.

### Exercise 6.3: expected improvement

Evaluate these limiting cases without code:

1. predicted mean 0.5, standard deviation 0, incumbent 1.0;
2. predicted mean 1.5, standard deviation 0, incumbent 1.0;
3. predicted mean 1.0, nonzero standard deviation, incumbent 1.0.

Explain how expected improvement balances exploitation and exploration. Then
explain what dividing it by $\sqrt{C_{\mathrm{index}}}$ changes.

### Exercise 6.4: fair comparison

List every quantity held equal between BO and random search. Your list must
include initial observations, candidate pool, follow-up budget, physical
evaluator, application objective, and current optimization.

Why would comparing 12 BO additions with only 5 random additions be invalid?
Why is the retrospective pool optimum allowed in the report but not as an
optimizer input?

### Exercise 6.5: interpret the curves

The 25 K utility changes from 3.9015 to 6.4268.

1. Calculate the percentage improvement.
2. At which additional prototype does BO reach the pool optimum in the figure?
3. What does the random median do?
4. What do the 10--90% random bands communicate that a single random seed
   cannot?

For both 10 K applications, the initial best equals the pool optimum.

5. Explain why a flat BO curve is correct in this case.
6. Explain why claiming “BO always improves the answer” would be false.

---

## Part 7: robustness and commercialization

### Exercise 7.1: nominal versus robust optimization

Define these two questions separately:

1. Which design has the highest utility at nominal parameters?
2. Which design has the highest utility while meeting requirements in at least
   95% of as-built cases?

Explain why the current campaign answers only the first during selection and
evaluates the second afterward.

### Exercise 7.2: the fragile efficiency winner

The nominal efficiency-first point delivers 2.524 W and the requirement is
2.5 W. Its Monte Carlo pass rate is 55.3%.

1. Calculate its nominal cooling margin in watts and percent.
2. Explain why its 5th-percentile COP can remain strong while the design fails
   the application requirement.
3. Which requirement is most likely causing failure?
4. Is 55.3% a measured manufacturing yield? Explain precisely.
5. Propose a chance constraint that would prevent this selection.

### Exercise 7.3: fixed current versus re-optimized current

1. Why does the robustness study keep the nominal current fixed?
2. What different question would be answered by re-optimizing current for every
   trial?
3. Which study is more relevant to a controller that can commission each unit?
4. Which is more relevant to a product with one fixed factory setpoint?

### Exercise 7.4: uncertainty model audit

For each uncertainty distribution, state a physical mechanism it might stand
in for and one reason its current numerical width could be wrong.

| Perturbation | Possible physical mechanism | Why width is unvalidated |
| --- | --- | --- |
| Seebeck |  |  |
| electrical conductivity |  |  |
| thermal conductivity |  |  |
| specific electrical contact resistivity |  |  |
| thermal contact resistance |  |  |
| exchanger conductance |  |  |
| converter efficiency |  |  |

---

## Part 8: code tracing and tests

### Exercise 8.1: map claims to tests

For each claim, find the exact test method and explain what failure would mean.

| Claim | Test method | Consequence of failure |
| --- | --- | --- |
| p and n Seebeck signs are correct |  |  |
| double $L$ doubles bulk $R$, leaves contact $R$ unchanged, and halves leg $K$ |  |  |
| selected current-density constraints are flagged as binding |  |  |
| every Latin-hypercube stratum is used |  |  |
| BO never selects the same candidate twice |  |  |
| best-so-far utility never decreases |  |  |
| robustness is reproducible |  |  |
| report output is a PNG |  |  |

### Exercise 8.2: find the deliberate guards

Find code that rejects:

1. p material with negative Seebeck coefficient;
2. zero leg area;
3. converter efficiency above one;
4. duplicate design IDs in a BO run;
5. negative GP standard deviation passed to expected improvement;
6. a BO budget larger than the candidate pool.

For each, write the incorrect consequence that could occur without the guard.

### Exercise 8.3: reproduce the report

Before running it, predict:

1. which application will show BO improvement;
2. which selected design will have the lowest robustness pass rate;
3. whether the capacity-first current will exceed the efficiency-first current.

Run:

```bash
python3 -m thermotwin.material_geometry_codesign_report
```

Record the printed results and figure path. Compare every prediction with the
result and explain any surprise.

### Exercise 8.4: small configuration experiment

Create a `CodesignCampaignConfig` with:

- 6 initial designs;
- 12 candidates;
- 2 BO additions;
- 3 random repetitions;
- 10 robustness trials;
- 8 current-grid points.

1. Run it without editing the package defaults.
2. Time the run.
3. Compare its winners with the full campaign.
4. Explain why a faster coarse experiment is useful for tests but should not
   replace the frozen report.

---

## Part 9: interpretation and proposed extensions

### Exercise 9.1: product recommendation memo

Write a 200-word recommendation to a thermoelectric product team. Include:

- which result is actionable now;
- why the high-lift BO result is promising;
- why the efficiency-first winner should not be released as-is;
- one piece of hardware data needed next;
- one sentence distinguishing virtual evidence from product validation.

### Exercise 9.2: add temperature-dependent properties on paper

The current material records are fixed at 300 K. Without coding, outline how
you would replace constant $S$, $\sigma$, and $k$ with temperature-dependent
curves.

1. At which temperatures would p- and n-leg properties be evaluated?
2. Would the steady equations remain linear?
3. What numerical solver would become necessary?
4. What new validation tests would you add?

### Exercise 9.3: process-aware optimization design

Design the dataset needed to optimize an SPS process rather than merely select
an existing material record. List:

- controllable process inputs;
- measured intermediate structure or quality variables;
- final $S$, $\sigma$, and $k$ measurements versus temperature;
- geometry and interface measurements;
- yield and repeatability data;
- cost and cycle-time data.

Explain why a sample label such as “SPS-250C” is not enough by itself to infer a
general process-to-property law.

### Exercise 9.4: robust Bayesian optimization extension

Propose a new acquisition target that values expected application utility but
requires at least 95% predicted feasibility.

1. What probabilistic model supplies feasibility probability?
2. How would prototype cost enter?
3. Would you keep one GP or use separate models for objective and constraints?
4. How would you compare the new selector fairly with the current nominal BO?

---

## Corrections log

Record conceptual or coding mistakes here rather than deleting them.

| Date | My original statement | Exact problem | Corrected reasoning | Test or equation that confirms it |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Final self-check

Without looking at the code, explain the entire campaign in this order:

1. source data;
2. same-row curation;
3. p/n pair and module scaling;
4. contact/exchanger/electrical model;
5. application constraints and objectives;
6. 24-design screen;
7. BO and random comparison;
8. selected designs and currents;
9. fixed-current uncertainty test;
10. strongest conclusion and strongest limitation.

Mark this note `Reviewed` only after the explanation, hand calculations, code,
tests, and report all agree.
