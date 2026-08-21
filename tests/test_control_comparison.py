import math
import unittest

from thermotwin.control_comparison import (
    ControlComparisonConfig,
    run_control_comparison,
    trapezoidal_integral,
)


class ControlComparisonTests(unittest.TestCase):
    def test_trapezoidal_integral_clips_both_interval_edges(self):
        value = trapezoidal_integral(
            (0.0, 1.0, 2.0),
            (0.0, 1.0, 2.0),
            start_time=0.5,
            end_time=1.5,
        )

        self.assertAlmostEqual(value, 1.0)

    def test_configuration_rejects_nonphysical_values(self):
        for keyword, value in (
            ("time_step", 0.0),
            ("pulse_duty_cycles", (1.0,)),
            ("maximum_current", -1.0),
        ):
            with self.subTest(keyword=keyword):
                with self.assertRaises(ValueError):
                    ControlComparisonConfig(**{keyword: value})

    def test_equal_capacity_comparison_reports_storage_and_safety(self):
        config = ControlComparisonConfig(
            warmup_duration=160.0,
            evaluation_duration=40.0,
            time_step=0.4,
            target_cooling_rates=(2.0,),
            pulse_periods=(10.0,),
            pulse_duty_cycles=(0.75,),
            maximum_storage_drift=0.2,
        )

        result = run_control_comparison(
            config,
            cold_contact_resistance_samples=(0.25,),
        )
        comparison = result.comparisons[0]

        self.assertLess(
            abs(comparison.continuous.average_cooling_rate - 2.0),
            config.cooling_match_tolerance,
        )
        self.assertLess(
            abs(comparison.best_pulsed.average_cooling_rate - 2.0),
            config.cooling_match_tolerance,
        )
        self.assertTrue(comparison.continuous.safe)
        self.assertTrue(comparison.best_pulsed.safe)
        self.assertTrue(comparison.continuous.cyclically_settled)
        self.assertTrue(comparison.best_pulsed.cyclically_settled)
        self.assertTrue(math.isfinite(comparison.pulsed_cop_change_percent))
        self.assertLess(
            abs(
                comparison.equal_power_continuous.average_electrical_power
                - comparison.best_pulsed.average_electrical_power
            ),
            0.001,
        )
        self.assertTrue(
            math.isfinite(
                comparison.pulsed_cooling_change_at_equal_power_percent
            )
        )
        self.assertEqual(len(result.uncertainty_cases), 1)


if __name__ == "__main__":
    unittest.main()
