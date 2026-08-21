# Exercise sheet 20 — Seconds-scale pulses on the steady COP envelope

## Purpose

Understand how the existing transient continuous-versus-pulsed study is placed
on the steady operating map, and why mean current, RMS current, settling, and
fair matching matter.

## Files to trace

- `thermotwin/control_comparison.py`
- `thermotwin/cop_operating_map.py`
- `thermotwin/pulse_operating_map.py`
- `thermotwin/pulse_operating_map_report.py`
- `tests/test_control_comparison.py`
- `tests/test_pulse_operating_map.py`
- `thermotwin/PULSE_OPERATING_MAP_EXPERIMENT.md`

## Part A — Prediction before execution

1. For a 1 A peak rectangular pulse at 25%, 50%, and 75% duty, calculate mean
   current, RMS current, and mean-square current.

2. At which duty is the difference between RMS and mean current greatest?

3. Compare continuous 0.75 A with a 1 A, 75% pulse. Which has the same mean
   Peltier term? Which has more average Joule heat, and by what factor?

4. Predict whether a nontrivial pulse will lie above or below the continuous
   COP envelope in the current constant-property model. Then predict what must
   happen as duty approaches one. Record physical reasons, not merely guesses.

5. Name one additional physical mechanism that could change your prediction.

## Part B — Fair objectives

6. Explain why comparing a 1 A continuous schedule with a 1 A peak pulse does
   not hold delivered cooling constant.

7. Explain why comparing schedules at equal mean current does not hold
   electrical power constant.

8. Define the two comparisons made by the code: equal delivered cooling and
   equal electrical power. What is measured in each direction?

9. Why is reservoir heat used as useful cooling instead of instantaneous
   module $Q_c$?

10. Construct an example in which a face cools temporarily because stored
    energy is falling. Why would counting this as steady useful cooling be
    misleading?

## Part C — Time averaging and settling

11. Write $P=\alpha(T_h-T_c)I+RI^2$ on both sides of an ideal current switch.
    Which quantities are continuous, and which quantity jumps?

12. Explain why directly applying an ordinary trapezoidal rule to one stored
    power value at each output time draws a fictitious ramp across that jump.
    How can this error depend on output-grid alignment?

13. Trace `piecewise_electrical_energy`. Explain why inserting schedule
    transitions and evaluating both endpoint powers with the interval current
    preserves the left and right limits. Why is a single forward interpolation
    pass preferable to repeatedly searching the full trajectory?

14. Write total stored energy for the four-node model. Differentiate it and
    explain the units of mean storage-energy drift.

15. Why is the 120 s evaluation duration convenient for periods 10, 20, 30,
    and 60 s?

16. Does a small final-minus-initial stored-energy drift guarantee every cycle
    is identical? What additional waveform check could strengthen settling?

## Part D — Trace the search

17. Follow `_continuous_point` through `_match_target`. Identify what
    bisection varies and what output it matches.

18. Follow `_pulse_point`. List the three independent pulse choices before
    amplitude matching.

19. Find all rejection conditions: reachability, current, temperature, and
    settling. Explain the consequence of omitting each one.

20. Read how `best_pulsed` is selected. Is the code minimizing power directly
    or maximizing a ratio after matching cooling?

21. Inspect `first_rising_crossing_bracket`. Sketch a cooling-versus-current
    curve that crosses a target and then falls below it before the configured
    maximum current. Why is checking only the endpoint incorrect?

22. In `run_pulse_operating_map`, explain why the continuous current is passed
    to the exact algebraic contact solver.

23. Derive `steady_map_cop_error_percent`. What value would make you distrust
    the warm-up interval?

## Part E — Run and analyze the result

Run:

```bash
python3 -m thermotwin.pulse_operating_map_report
```

24. Record the continuous and highest-COP tested COP at 2, 5, and 8 W.
    Calculate one COP percentage change independently.

25. For the 5 W, 99%-duty point, verify that 0.5928 A peak gives approximately
    0.5869 A mean and 0.5898 A RMS.

26. Compare that pulse mean with the 0.5866 A continuous current.
    Why does a similar mean current not imply similar COP?

27. The steady-map COP mismatch is below 0.04%. State what that validates and
    what it does not validate.

28. At the 5 W target, record COP change at duties 0.50, 0.75, 0.90, 0.95,
    and 0.99. Explain why the old 75%-capped headline was a grid-corner result.

29. Starting from equal mean current, prove that direct rectangular pulsing
    multiplies Joule heat by $1/D$. Explain why the full matched-cooling COP
    penalty need not equal that multiplier exactly.

30. Compare the equal-cooling and equal-power penalty curves. Why do the
    percentage values differ even though both favor continuous control?

31. Confirm every reported storage drift is below 0.05 W. Explain why a
    passing drift check supports, but does not prove, hardware relevance.

## Part F — Seconds-scale pulse versus PWM

32. Explain why a 10 s pulse must be resolved by the thermal integrator.

33. Explain why a 20 kHz electrical switch should not normally force the same
    four thermal states to be integrated at 20 kHz.

34. What electrical information is lost if high-frequency PWM is replaced
    only by mean current?

35. What extra current statistic captures Joule heating?

36. Make a two-column table distinguishing thermal pulse optimization and
    switch-mode power conversion by time scale, state response, equations, and
    objective.

## Part G — Tests and extensions

37. Find the tests that reproduce switch-aware power integration on coarse and
    switch-misaligned grids. State the failure signature of the old method.

38. Find the test that checks RMS current exceeds mean current. Explain the
    limiting result at duty one.

39. Find the test that requires pulse COP below continuous COP. Is this a
    universal physics law or a frozen regression result? Explain why that
    distinction matters.

40. Design a test for a pulse whose evaluation interval contains a noninteger
    number of periods. What bias do you expect?

41. Design a new experiment that varies external lift while holding one useful
    cooling target. Specify what becomes infeasible first.

42. Propose one closed-loop objective other than steady cooling COP, such as
    peak temperature, comfort error, or demand response. State what additional
    model inputs it needs.

## Part H — Own explanation

43. Explain the duty-law result without saying “pulsing is bad.”

44. Write the exact scope sentence that prevents this synthetic result from
    becoming a claim about a different physical product.

45. Record corrections to your initial predictions.

46. Status after review: `Not started`, `Draft`, `Revising`, or `Reviewed`.
