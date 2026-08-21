# Exercise sheet 19 — COP operating maps

## Purpose

Use this sheet to understand both the thermal physics and the code behind the
cooling/heating current, temperature-lift, and contact-resistance maps.

Do the prediction sections before running the report. Record corrections
rather than erasing an incorrect first prediction.

## Files to trace

- `thermotwin/thermoelectric.py`
- `thermotwin/transient.py`
- `thermotwin/contact_transient.py`
- `thermotwin/cop_operating_map.py`
- `thermotwin/cop_operating_map_report.py`
- `tests/test_cop_operating_map.py`
- `tests/test_contact_transient.py`
- `thermotwin/COP_OPERATING_MAP_EXPERIMENT.md`

## Part A — Define the experiment before calculating

1. Define external, exchanger, and face temperature lift in words and symbols.
   Which temperatures would a fluid loop most directly expose? Which ones enter
   $Q_c$ and $Q_h$?

2. For mean reservoir temperature 300 K and external lift 20 K, calculate both
   reservoir temperatures.

3. Explain why a positive contact heat flow requires a temperature drop across
   a positive contact resistance.

4. Predict whether the face lift will be smaller than, equal to, or larger
   than the external lift while useful cooling is delivered. State the heat
   directions you used.

5. Why is “no explicit contact model” a topology choice rather than
   `contact_resistance=0` in the four-node equations?

## Part B — Cooling and heating COP

6. Starting from $Q_h-Q_c=VI$, derive the relation between heating and cooling
   COP when both useful rates are positive and the system is at steady state.

7. Does $\mathrm{COP}_h=\mathrm{COP}_c+1$ mean heating COP must always be
   greater than one? Identify the assumptions needed for that statement.

8. At a point with 3 W delivered cooling and 1.5 W electrical power, calculate
   cooling COP, delivered heating, and heating COP.

9. Suppose electrical power approaches zero and useful heat also approaches
   zero. Explain why the ratio can become large without describing a useful
   high-capacity operating point.

10. Defend or revise the experiment's rule that a reported maximum COP must
    deliver at least 1 W. What other threshold could a hardware study use?

## Part C — Predict the curves

Before opening the figure, draw qualitative curves and answer:

11. At fixed lift, what happens to Peltier cooling and Joule heating when
    current doubles?

12. Predict the current that maximizes COP relative to the current that
    maximizes cooling capacity. Explain why they need not coincide.

13. Predict how the useful cooling threshold current changes as external lift
    increases from 0 to 30 K.

14. Predict how raising both contacts from 0.10 to 0.50 K/W changes:
    face lift, delivered cooling at fixed current, current required for fixed
    cooling, and COP.

15. At a fixed 1.5 A limit, predict what can make a 3 W target infeasible.

## Part D — Derive the steady solver

Use the order $[T_c,T_h,T_{x,c},T_{x,h}]$.

16. Set each of the four transient energy balances to zero.

17. Substitute
    $Q_c=\alpha I T_c-I^2R/2-K(T_h-T_c)$ into the cold-face balance and
    collect the four temperature coefficients.

18. Repeat for the hot-face balance. Check carefully why the coefficient of
    $T_h$ contains $-\alpha I$ after the equation is rearranged into the
    implemented matrix form.

19. Derive both exchanger rows. Which entries are zero, and what physical
    missing connection does each zero represent?

20. Show why capacitances disappear from the steady matrix. Do they become
    physically irrelevant, or do they still control something else?

21. Inspect `four_node_contact_steady_state`. Match every matrix coefficient
    and right-hand-side term to your derivation.

## Part E — Trace the operating-map code

22. In `COPOperatingMapConfig`, identify the four independent sweep or
    constraint choices. Which are physical parameters and which are experiment
    design decisions?

23. Trace one call from `run_cop_operating_map` to
    `contact_steady_operating_point`. List every output calculated after the
    four temperatures are solved.

24. Explain the two `math.isclose` checks between delivered and module heat.
    What exact sign or equation bug could each detect?

25. Read `_optimal_summary`. Show exactly how a sub-1 W point is excluded.

26. Read `_match_heat_rate` and `first_rising_crossing_bracket`. Why is testing
    feasibility only at `maximum_current` unsafe once cooling has a
    high-current turnover? Explain how the coarse scan locates the first rising
    target crossing and why bisection is then valid only inside that bracket.
    Find the regression test whose 12 A endpoint is below a feasible 3 W
    target.

27. Why does the equal-load comparison solve for different currents instead
    of comparing both topologies at 1 A?

28. Calculate the expected point count from 7 lifts, 30 currents, and four
    topologies. Confirm it in code.

## Part F — Run and interpret

Run:

```bash
python3 -m thermotwin.cop_operating_map_report
```

29. At 10 K lift and 0.25 K/W contacts, record the best useful cooling COP,
    current, and cooling rate. Was your predicted optimum current too high or
    too low?

30. At equal 3 W cooling, calculate the percentage COP change from 2.316 to
    1.836. Explain why the contact case also requires more current.

31. Compare the 0.10, 0.25, and 0.50 K/W penalty curves. Is the percentage
    penalty linear in resistance? Use the thermal equations to explain why a
    linear contact law need not produce a linear system-level COP change.

32. At 20 K lift, why can cooling COP be below one while heating COP is above
    one?

33. At 30 K, identify the difference between “some positive cooling exists”
    and “the 3 W target is feasible.”

34. Write a four-sentence investor-safe summary that states the generic result,
    contact penalty, useful design implication, and hardware limitation.

## Part G — Tests and limiting cases

35. Locate the test for $\mathrm{COP}_h=\mathrm{COP}_c+1$. What would fail if
    $Q_h$ used cold temperature in its Peltier term?

36. Locate the test that approaches the algebraic state with RK4. Why is
    testing only the four zero RHS values insufficient as an independent
    numerical check?

37. Explain why changing all four capacitances must leave the algebraic steady
    solution unchanged.

38. Predict the contact-aware solution as contact resistance becomes small.
    Why does the implementation not test the exact zero value?

39. Add, on paper first, a test that verifies a larger external lift lowers
    delivered cooling at fixed current for one stated reference point. State
    why this should not be generalized without conditions.

40. Design one test that would prevent the report from labeling a negative
    cold-side heat rate as cooling COP.

## Part H — Corrections and own explanation

41. Record one prediction that the result contradicted.

42. Explain the entire map without using the words “just,” “obvious,” or
    “because the code says so.”

43. List three pieces of hardware data needed before comparing this map with a
    physical thermoelectric HVAC product.

44. Status after review: `Not started`, `Draft`, `Revising`, or `Reviewed`.
