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

4. Predict whether the optimized pulse will lie above or below the continuous
   COP envelope in the current constant-property model. Record a physical
   reason, not merely a guess.

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

11. Write the trapezoidal approximation used to integrate sampled power.

12. Inspect `trapezoidal_integral`. Why must it interpolate when the evaluation
    boundary falls inside one stored step?

13. Write total stored energy for the four-node model. Differentiate it and
    explain the units of mean storage-energy drift.

14. Why is the 120 s evaluation duration convenient for periods 10, 20, 30,
    and 60 s?

15. Does a small final-minus-initial stored-energy drift guarantee every cycle
    is identical? What additional waveform check could strengthen settling?

## Part D — Trace the search

16. Follow `_continuous_point` through `_match_target`. Identify what
    bisection varies and what output it matches.

17. Follow `_pulse_point`. List the three independent pulse choices before
    amplitude matching.

18. Find all rejection conditions: reachability, current, temperature, and
    settling. Explain the consequence of omitting each one.

19. Read how `best_pulsed` is selected. Is the code minimizing power directly
    or maximizing a ratio after matching cooling?

20. In `run_pulse_operating_map`, explain why the continuous current is passed
    to the exact algebraic contact solver.

21. Derive `steady_map_cop_error_percent`. What value would make you distrust
    the warm-up interval?

## Part E — Run and analyze the result

Run:

```bash
python3 -m thermotwin.pulse_operating_map_report
```

22. Record the continuous and pulse COP at 2, 5, and 8 W. Calculate one COP
    percentage change independently.

23. For the 5 W winner, verify 0.8006 A peak at 75% duty gives approximately
    0.6005 A mean and 0.6934 A RMS.

24. Compare that 0.6005 A pulse mean with the 0.5866 A continuous current.
    Why does a similar mean current not imply similar COP?

25. The steady-map COP mismatch is below 0.04%. State what that validates and
    what it does not validate.

26. The pulse COP penalty becomes larger from 2 to 8 W. Relate that trend to
    peak and RMS current.

27. Compare the equal-cooling and equal-power penalty curves. Why do the
    percentage values differ even though both favor continuous control?

28. Confirm every reported storage drift is below 0.05 W. Explain why a
    passing drift check supports, but does not prove, hardware relevance.

## Part F — Seconds-scale pulse versus PWM

29. Explain why a 10 s pulse must be resolved by the thermal integrator.

30. Explain why a 20 kHz electrical switch should not normally force the same
    four thermal states to be integrated at 20 kHz.

31. What electrical information is lost if high-frequency PWM is replaced
    only by mean current?

32. What extra current statistic captures Joule heating?

33. Make a two-column table distinguishing thermal pulse optimization and
    switch-mode power conversion by time scale, state response, equations, and
    objective.

## Part G — Tests and extensions

34. Find the test that checks RMS current exceeds mean current. Explain the
    limiting result at duty one.

35. Find the test that requires pulse COP below continuous COP. Is this a
    universal physics law or a frozen regression result? Explain why that
    distinction matters.

36. Design a test for a pulse whose evaluation interval contains a noninteger
    number of periods. What bias do you expect?

37. Design a new experiment that varies external lift while holding one useful
    cooling target. Specify what becomes infeasible first.

38. Propose one closed-loop objective other than steady cooling COP, such as
    peak temperature, comfort error, or demand response. State what additional
    model inputs it needs.

## Part H — Own explanation

39. Explain the negative result without saying “pulsing is bad.”

40. Write the exact scope sentence that prevents this synthetic result from
    becoming a claim about a different physical product.

41. Record corrections to your initial predictions.

42. Status after review: `Not started`, `Draft`, `Revising`, or `Reviewed`.
