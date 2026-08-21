# Exercise sheet 21 — Averaged PWM and power electronics

## Purpose

Understand why thermoelectric PWM requires both mean and mean-square current,
how smoothed and directly chopped current differ, and how module power differs
from wall-plug power in the code.

## Files to trace

- `thermotwin/pwm_power_electronics.py`
- `thermotwin/pwm_power_electronics_report.py`
- `tests/test_pwm_power_electronics.py`
- `thermotwin/PWM_POWER_ELECTRONICS_EXPERIMENT.md`

## Part A — Current moments by hand

1. Sketch direct PWM current alternating between 0 and 1.5 A at duty 0.4.
   Calculate mean current, mean-square current, and RMS current.

2. Calculate the direct-PWM Joule multiplier over DC at duties 0.1, 0.25,
   0.5, and 1.0.

3. For 0.6 A mean current with 10% peak-to-peak triangular ripple, calculate
   $\Delta I_{pp}$ and $\overline{I^2}$.

4. Show that the smoothed Joule multiplier is $1+r^2/12$. Evaluate it for
   ripple fractions 0%, 10%, 50%, and 100%.

5. Explain physically why equal mean current does not imply equal copper or
   module resistive heating.

## Part B — Derive averaged thermoelectric heat

6. Average the Peltier term $\alpha I(t)T_c$ over one electrical cycle while
   treating $T_c$ as constant during that cycle.

7. Average the Joule term $I(t)^2R/2$. Why can it not be calculated from only
   $\overline I$?

8. Write averaged $Q_c$, $Q_h$, and module power in terms of $\overline I$ and
   $\overline{I^2}$.

9. Subtract your heat equations and prove
   $\overline Q_h-\overline Q_c=\overline P_{\mathrm{module}}$.

10. Starting from $\overline{IT}$, derive
    $\overline{IT}=\overline I\,\overline T+\mathrm{Cov}(I,T)$. Identify the
    time-scale assumption used when the code sets the covariance term to zero.

11. Give an example in which that assumption could fail. What additional
    electrothermal output would be needed besides the first two current
    moments?

## Part C — Converter and COP boundaries

12. Distinguish module terminal power from supply power in words and with the
    implemented equation.

13. For 1 W module power, 95% efficiency, and 0.05 W fixed loss, calculate
    supply power.

14. If useful cooling is 2 W, calculate module COP and wall COP for the power
    in exercise 13.

15. Explain why fixed converter loss has a larger percentage effect at low
    module power.

16. Heating COP can rise when extra Joule heat is added. Explain why this can
    represent resistance heating rather than improved heat pumping.

17. Explain why the ideal DC case deliberately has no converter loss. What
    additional comparison would be needed to compare two real converter
    designs fairly?

## Part D — Trace the current-model code

18. Inspect `CurrentMoments`. Map each field to a physical quantity and unit.

19. Trace `direct_pwm_current_moments`. Derive every returned expression.

20. Trace `smoothed_pwm_current_moments`. Where does the factor 12 come from?

21. Explain the limiting cases:
    direct duty one, smoothed ripple zero, and converter efficiency one with
    zero fixed loss.

22. Find the validation that prevents mean current from exceeding direct peak
    current. What would a duty greater than one mean?

## Part E — Trace the thermal coupling

23. Trace `averaged_contact_steady_state` into
    `four_node_contact_steady_state_from_current_moments`, then trace scalar
    `four_node_contact_steady_state` into the same helper. Identify how the
    helper represents Peltier and Joule terms and explain why sharing this
    matrix prevents the DC, PWM, and co-design implementations from drifting.

24. Why does $\alpha I$ use mean current while half-Joule heat uses
    mean-square current?

25. Find the current-moment validation that enforces
    $\overline{I^2}\geq\overline I^2$. Name the inequality behind it and give
    an impossible moment pair that must be rejected.

26. Explain why no switching frequency appears in the current implementation.
    Is that an omission, an averaging choice, or both?

27. Trace supply power selection for `ideal_dc`, `smoothed_pwm`, and
    `direct_pwm`.

28. Explain why module COP and wall COP are both retained instead of replacing
    one with the other.

## Part F — Predict then run

Before running, predict the ordering of delivered cooling and wall cooling COP
for the three current modes at 0.6 A mean and 10 K lift.

Run:

```bash
python3 -m thermotwin.pwm_power_electronics_report
```

29. Compare your ordering with the result.

30. Verify the direct-PWM duty and Joule multiplier at 0.6 A mean and 1.5 A
    peak.

31. At 10 K lift, calculate the direct-PWM delivered-cooling change relative
    to the smoothed case.

32. Calculate the smoothed and direct wall-COP changes relative to ideal DC.

33. At 20 K and 0.6 A, explain the sign of delivered cooling. Why is cooling
    COP omitted rather than shown as a negative efficiency?

34. Find a current on the 20 K plot where useful cooling becomes positive.
    Explain the threshold using Peltier, Joule, and conduction terms.

35. Explain why the direct-PWM COP penalty becomes less severe as mean current
    approaches the fixed 1.5 A peak.

## Part G — Tests and model honesty

36. Locate the energy-identity test. Change one half-Joule sign on paper and
    predict its failure value.

37. Locate the full-duty direct-PWM limiting test. Why does it compare module
    physics but not wall COP?

38. Locate the zero-ripple test. What converter loss remains even when ripple
    becomes zero?

39. Explain why the frozen regression “direct PWM is worse at 0.6 A and 10 K”
    is not a universal theorem about every controlled system.

40. Find the scalar-current limiting test for the shared moment solver. Why
    must using $(\overline I,\overline{I^2})=(I,I^2)$ reproduce the original
    four-node steady state?

41. Design a test that verifies increasing converter efficiency increases
    wall COP without changing face temperatures or module COP.

## Part H — Next electrical model

42. List the electrical parameters required to predict current ripple instead
    of prescribing it: include at least input voltage, switching frequency,
    inductance, load resistance, and control law.

43. List losses absent from the constant efficiency model.

44. Propose an RMS-current or semiconductor-temperature constraint and explain
    where it would enter an optimization.

45. Design one measurement set that could calibrate converter efficiency as a
    function of voltage, current, and duty.

46. Explain how a detailed converter could still pass only $\overline I$ and
    $\overline{I^2}$ to a slow thermal model.

47. Under what condition are those two moments insufficient because
    current-temperature covariance is no longer negligible?

## Part I — Own explanation and corrections

48. Explain the difference between direct current PWM and smoothed PWM-derived
    current to someone who knows basic circuits but not thermoelectrics.

49. Explain why “just use a shorter thermal time step” is not a complete
    power-electronics model.

50. Record one prediction you revised after viewing the result.

51. State three limitations before using these numbers in a product decision.

52. Status after review: `Not started`, `Draft`, `Revising`, or `Reviewed`.
