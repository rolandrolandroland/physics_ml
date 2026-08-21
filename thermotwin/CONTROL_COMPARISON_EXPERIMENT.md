# Continuous-versus-pulsed control experiment

## Question

At the same delivered cooling rate, does periodic current improve cooling COP
over an optimized continuous-current baseline in the current four-node
ThermoTwin model?

The pulse is allowed to win, tie, or lose. The comparison is intentionally
structured to prevent a transient pulse from receiving credit for temporarily
draining energy stored in the faces or exchangers.

## Useful cooling and electrical input

The reported useful cooling is heat extracted from the fixed cold reservoir,

$$
\overline{\dot Q}_{\mathrm{useful}}
=\frac{1}{\Delta t}\int_{t_0}^{t_1}
G_c\left(T_{c,\infty}-T_{x,c}\right)\,dt.
$$

This differs from instantaneous module-side $Q_c$. It represents the heat the
cold reservoir supplies to the cooled exchanger over the evaluation window.

Average electrical input and delivered cooling COP are

$$
\overline P_e=\frac{1}{\Delta t}\int_{t_0}^{t_1}V(t)I(t)\,dt,
\qquad
\mathrm{COP}_{\mathrm{delivered}}
=\frac{\overline{\dot Q}_{\mathrm{useful}}}{\overline P_e}.
$$

The code also evaluates the net change of energy stored in all four thermal
capacitances. A schedule is accepted only when its mean storage drift is below
0.05 W over the comparison window.

## Fair comparison procedure

1. Warm every candidate for 360 s.
2. Evaluate the next 120 s, which is divisible by all tested pulse periods.
3. For each target cooling rate, solve for the continuous current that meets
   the target.
4. Sweep pulse periods of 10, 20, 30, and 60 s and duty cycles of 0.25, 0.50,
   and 0.75.
5. For every pulse shape, solve for the pulse amplitude that meets the same
   target cooling rate.
6. Reject shapes that cannot reach the target below 1.5 A, violate the
   285--315 K face-temperature limits, or fail the storage-drift check.
7. Compare the highest-COP feasible pulse with the optimized continuous case.

The RK4 reference solver is used because it is faster and more accurate for a
large control sweep than retraining a per-experiment PINN.

## Result

| Delivered cooling | Continuous current | Continuous COP | Best pulse | Best pulse COP | Pulse COP change |
| ---: | ---: | ---: | --- | ---: | ---: |
| 2 W | 0.2231 A | 15.6014 | 0.3000 A, 10 s, 75% duty | 12.1968 | -21.82% |
| 5 W | 0.5866 A | 5.6543 | 0.8006 A, 10 s, 75% duty | 4.2873 | -24.18% |
| 8 W | 0.9945 A | 3.1518 | 1.3897 A, 10 s, 75% duty | 2.2808 | -27.64% |

Four pulse shapes cannot reach 5 W under the current limit; eight cannot reach
8 W. All reported winners satisfy the temperature and periodic-storage
checks.

The result is negative for pulsing: optimized continuous current has higher
COP at all three matched capacities. In this constant-property lumped model,
the quadratic Joule penalty from higher pulse amplitude outweighs any benefit
from the transient temperature response.

The conclusion is the same when the comparison direction is reversed. Holding
electrical power equal to each best pulse, optimized continuous current
delivers more cooling:

| Pulse cooling | Continuous cooling at the same power | Pulse cooling change |
| ---: | ---: | ---: |
| 2.0000 W | 2.2532 W | -11.23% |
| 5.0000 W | 5.6735 W | -11.88% |
| 8.0000 W | 9.1702 W | -12.76% |

That conclusion is useful. It identifies which additional physics would need
evidence before claiming a pulse advantage, such as flow-dependent heat
transfer, spatial module dynamics, temperature-dependent properties,
multi-assembly staging, or a different building-side objective.

## Resistance-uncertainty stress test

The fixed 5 W schedules were reevaluated at the sparse-inference resistance
interval endpoints, 0.23861 and 0.26139 K/W, as well as its central estimate.
The pulse COP changes were -24.20%, -24.18%, and -24.16%. The qualitative
conclusion is therefore stable across the current resistance uncertainty.

This is not a claim that the conclusion is stable to every uncertain thermal
parameter.

## Reproduce

```bash
python3 -m thermotwin.control_comparison
```

The implementation is in [`control_comparison.py`](control_comparison.py).
The tests verify clipped integration, equal-capacity matching, safety, and
storage checks in
[`../tests/test_control_comparison.py`](../tests/test_control_comparison.py).

## Limitations

- Fixed reservoir temperatures replace flowing-fluid inlet/outlet states.
- Material properties are temperature independent.
- The model contains one assembly rather than a staged multi-assembly system.
- The comparison optimizes simple rectangular pulses, not arbitrary control
  waveforms or closed-loop comfort control.
- Synthetic results should not be interpreted as contradicting or validating
  performance claims for a different physical device.
