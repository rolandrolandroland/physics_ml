import math
import unittest

from thermotwin.material_geometry_codesign import (
    APPLICATION_SPECIFICATIONS,
    CodesignCampaignConfig,
    design_features,
    evaluate_design_current,
    expected_improvement,
    gaussian_process_predict,
    generate_space_filling_designs,
    latin_hypercube,
    optimize_design_current,
    run_bayesian_optimization,
    run_codesign_campaign,
    run_robustness_study,
)


class SpaceFillingDesignTests(unittest.TestCase):
    def test_latin_hypercube_uses_every_stratum_once_per_dimension(self):
        count = 12
        rows = latin_hypercube(count, 4, seed=9)
        self.assertEqual(rows, latin_hypercube(count, 4, seed=9))
        self.assertNotEqual(rows, latin_hypercube(count, 4, seed=10))
        for dimension in range(4):
            strata = sorted(int(row[dimension] * count) for row in rows)
            self.assertEqual(strata, list(range(count)))

    def test_design_generator_is_reproducible_and_inside_envelope(self):
        designs = generate_space_filling_designs(24, seed=2, prefix="test")
        self.assertEqual(designs, generate_space_filling_designs(24, seed=2, prefix="test"))
        self.assertEqual(len({design.design_id for design in designs}), 24)
        for design in designs:
            self.assertGreaterEqual(design.geometry.couple_count, 80)
            self.assertLessEqual(design.geometry.couple_count, 160)
            self.assertGreaterEqual(design.geometry.leg_length, 0.8e-3)
            self.assertLessEqual(design.geometry.leg_length, 2.4e-3)
            self.assertGreaterEqual(design.geometry.leg_area, 0.8e-6)
            self.assertLessEqual(design.geometry.leg_area, 2.4e-6)
            self.assertGreaterEqual(design.symmetric_contact_resistance, 0.10)
            self.assertLessEqual(design.symmetric_contact_resistance, 0.50)
            self.assertEqual(len(design_features(design)), 18)


class OperatingEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.design = generate_space_filling_designs(1, seed=4, prefix="one")[0]
        self.application = APPLICATION_SPECIFICATIONS[0]

    def test_steady_operating_point_closes_power_and_temperature_outputs(self):
        point = evaluate_design_current(self.design, self.application, 0.4)
        self.assertTrue(all(math.isfinite(value) for value in point[4:14] if value is not None))
        self.assertGreater(point.supply_electrical_power, point.module_electrical_power)
        self.assertGreater(point.prototype_cost_index, 0.0)
        self.assertGreater(point.peak_current, point.mean_current)

    def test_current_optimizer_returns_a_grid_point_with_maximal_utility(self):
        selected = optimize_design_current(self.design, self.application, grid_size=8)
        maximum_mean_current = 1.0e6 * self.design.geometry.leg_area / 1.05
        minimum_current = min(0.05, 0.05 * maximum_mean_current)
        currents = tuple(
            minimum_current + (maximum_mean_current - minimum_current) * index / 7
            for index in range(8)
        )
        points = tuple(
            evaluate_design_current(self.design, self.application, current)
            for current in currents
        )
        self.assertAlmostEqual(selected.utility, max(point.utility for point in points))


class BayesianOptimizationTests(unittest.TestCase):
    def test_gp_nearly_interpolates_training_values_and_has_nonnegative_spread(self):
        features = ((0.0,), (0.5,), (1.0,))
        values = (0.0, 1.0, 0.0)
        for feature, expected in zip(features, values):
            mean, standard_deviation = gaussian_process_predict(features, values, feature)
            self.assertAlmostEqual(mean, expected, delta=2e-3)
            self.assertGreaterEqual(standard_deviation, 0.0)
            self.assertLess(standard_deviation, 0.01)

    def test_expected_improvement_limiting_cases(self):
        self.assertEqual(expected_improvement(0.5, 0.0, 1.0), 0.0)
        self.assertEqual(expected_improvement(1.5, 0.0, 1.0), 0.5)
        self.assertGreater(expected_improvement(1.0, 0.2, 1.0), 0.0)

    def test_bayesian_campaign_is_reproducible_and_budgeted(self):
        initial = generate_space_filling_designs(6, seed=11, prefix="initial")
        candidates = generate_space_filling_designs(12, seed=12, prefix="candidate")
        arguments = dict(
            application=APPLICATION_SPECIFICATIONS[1],
            initial_designs=initial,
            candidate_designs=candidates,
            iterations=3,
            random_repetitions=4,
            seed=13,
            current_grid_size=7,
        )
        result = run_bayesian_optimization(**arguments)
        repeated = run_bayesian_optimization(**arguments)
        self.assertEqual(result, repeated)
        self.assertEqual(len(result.initial_evaluations), 6)
        self.assertEqual(len(result.acquired_evaluations), 3)
        self.assertEqual(len(result.best_utility_history), 4)
        self.assertEqual(
            len({point.design.design_id for point in result.acquired_evaluations}),
            3,
        )
        self.assertTrue(all(
            later >= earlier
            for earlier, later in zip(
                result.best_utility_history,
                result.best_utility_history[1:],
            )
        ))
        self.assertLessEqual(result.selected.utility, result.oracle_best.utility)

    def test_robustness_is_reproducible_and_keeps_nominal_current(self):
        design = generate_space_filling_designs(1, seed=5, prefix="robust")[0]
        nominal = optimize_design_current(design, APPLICATION_SPECIFICATIONS[0], grid_size=8)
        result = run_robustness_study(nominal, trials=20, seed=6)
        self.assertEqual(result, run_robustness_study(nominal, trials=20, seed=6))
        self.assertEqual(result.trial_count, 20)
        self.assertGreaterEqual(result.feasible_fraction, 0.0)
        self.assertLessEqual(result.feasible_fraction, 1.0)
        for quantiles in (
            result.cooling_rate_quantiles,
            result.wall_cop_quantiles,
            result.hot_face_temperature_quantiles,
        ):
            self.assertLessEqual(quantiles[0], quantiles[1])
            self.assertLessEqual(quantiles[1], quantiles[2])

    def test_small_end_to_end_campaign_has_all_three_experiments(self):
        config = CodesignCampaignConfig(
            initial_design_count=5,
            candidate_design_count=8,
            bayesian_iterations=2,
            random_search_repetitions=3,
            robustness_trials=6,
            current_grid_size=6,
        )
        result = run_codesign_campaign(config)
        self.assertEqual(len(result.initial_summaries), 3)
        self.assertEqual(len(result.bayesian_results), 3)
        self.assertEqual(len(result.robustness_results), 3)


if __name__ == "__main__":
    unittest.main()
