import unittest

from thermotwin import (
    FourNodeContactThermalParameters,
    PiecewiseConstantCurrent,
    ThermoelectricParameters,
    TwoNodeThermalParameters,
    electrical_power,
    four_node_contact_rhs,
    integrate_four_node_contact,
    integrate_two_node,
    thermal_contact_heat,
)


class ContactTransientTests(unittest.TestCase):
    def setUp(self):
        self.thermoelectric = ThermoelectricParameters(
            seebeck_coefficient=0.05,
            electrical_resistance=2.0,
            thermal_conductance=0.5,
        )
        self.thermal = FourNodeContactThermalParameters(
            cold_face_thermal_capacitance=50.0,
            hot_face_thermal_capacitance=100.0,
            cold_exchanger_thermal_capacitance=50.0,
            hot_exchanger_thermal_capacitance=100.0,
            cold_contact_resistance=0.5,
            hot_contact_resistance=0.25,
            cold_reservoir_conductance=2.0,
            hot_reservoir_conductance=4.0,
        )

    def test_contact_heat_sign_and_units_example(self):
        self.assertEqual(thermal_contact_heat(300.0, 295.0, 0.5), 10.0)
        self.assertEqual(thermal_contact_heat(295.0, 300.0, 0.5), -10.0)
        self.assertEqual(thermal_contact_heat(305.0, 300.0, 0.25), 20.0)

    def test_contact_heat_rejects_invalid_inputs(self):
        invalid_cases = (
            (300.0, 295.0, 0.0),
            (300.0, 295.0, -1.0),
            (300.0, 295.0, float("inf")),
            (300.0, 295.0, float("nan")),
            (float("nan"), 295.0, 1.0),
            (300.0, float("inf"), 1.0),
        )
        for values in invalid_cases:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    thermal_contact_heat(*values)

    def test_rhs_matches_hand_calculated_four_node_rates(self):
        rates = four_node_contact_rhs(
            self.thermoelectric,
            self.thermal,
            cold_face_temperature=295.0,
            hot_face_temperature=305.0,
            cold_exchanger_temperature=300.0,
            hot_exchanger_temperature=300.0,
            current=1.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
            cold_external_heat=3.0,
            hot_external_heat=-4.0,
        )

        self.assertAlmostEqual(rates.cold_face, 0.025)
        self.assertAlmostEqual(rates.hot_face, -0.0875)
        self.assertAlmostEqual(rates.cold_exchanger, -0.14)
        self.assertAlmostEqual(rates.hot_exchanger, 0.16)

    def test_whole_system_energy_rate_includes_only_external_exchange(self):
        inputs = dict(
            cold_face_temperature=294.0,
            hot_face_temperature=308.0,
            cold_exchanger_temperature=299.0,
            hot_exchanger_temperature=303.0,
            current=1.2,
            cold_reservoir_temperature=301.0,
            hot_reservoir_temperature=310.0,
            cold_external_heat=3.0,
            hot_external_heat=-4.0,
        )
        rates = four_node_contact_rhs(
            self.thermoelectric,
            self.thermal,
            **inputs,
        )

        stored_energy_rate = (
            self.thermal.cold_face_thermal_capacitance * rates.cold_face
            + self.thermal.hot_face_thermal_capacitance * rates.hot_face
            + self.thermal.cold_exchanger_thermal_capacitance
            * rates.cold_exchanger
            + self.thermal.hot_exchanger_thermal_capacitance
            * rates.hot_exchanger
        )
        expected_energy_rate = (
            self.thermal.cold_reservoir_conductance
            * (
                inputs["cold_reservoir_temperature"]
                - inputs["cold_exchanger_temperature"]
            )
            + self.thermal.hot_reservoir_conductance
            * (
                inputs["hot_reservoir_temperature"]
                - inputs["hot_exchanger_temperature"]
            )
            + inputs["cold_external_heat"]
            + inputs["hot_external_heat"]
            + electrical_power(
                self.thermoelectric,
                inputs["current"],
                inputs["hot_face_temperature"],
                inputs["cold_face_temperature"],
            )
        )

        self.assertAlmostEqual(stored_energy_rate, expected_energy_rate)

    def test_equal_temperatures_with_no_current_are_equilibrium(self):
        rates = four_node_contact_rhs(
            self.thermoelectric,
            self.thermal,
            cold_face_temperature=300.0,
            hot_face_temperature=300.0,
            cold_exchanger_temperature=300.0,
            hot_exchanger_temperature=300.0,
            current=0.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )

        self.assertEqual(rates, (0.0, 0.0, 0.0, 0.0))

    def test_contact_only_flow_has_opposite_pairwise_energy_rates(self):
        no_module_effects = ThermoelectricParameters(
            seebeck_coefficient=0.0,
            electrical_resistance=0.0,
            thermal_conductance=0.0,
        )
        insulated = FourNodeContactThermalParameters(
            cold_face_thermal_capacitance=50.0,
            hot_face_thermal_capacitance=100.0,
            cold_exchanger_thermal_capacitance=50.0,
            hot_exchanger_thermal_capacitance=100.0,
            cold_contact_resistance=0.5,
            hot_contact_resistance=0.25,
            cold_reservoir_conductance=0.0,
            hot_reservoir_conductance=0.0,
        )
        rates = four_node_contact_rhs(
            no_module_effects,
            insulated,
            cold_face_temperature=290.0,
            hot_face_temperature=310.0,
            cold_exchanger_temperature=310.0,
            hot_exchanger_temperature=290.0,
            current=0.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )

        self.assertGreater(rates.cold_face, 0.0)
        self.assertLess(rates.cold_exchanger, 0.0)
        self.assertLess(rates.hot_face, 0.0)
        self.assertGreater(rates.hot_exchanger, 0.0)
        self.assertAlmostEqual(
            insulated.cold_face_thermal_capacitance * rates.cold_face
            + insulated.cold_exchanger_thermal_capacitance
            * rates.cold_exchanger,
            0.0,
        )
        self.assertAlmostEqual(
            insulated.hot_face_thermal_capacitance * rates.hot_face
            + insulated.hot_exchanger_thermal_capacitance
            * rates.hot_exchanger,
            0.0,
        )

    def test_current_reversal_flips_peltier_face_rates(self):
        peltier_only = ThermoelectricParameters(
            seebeck_coefficient=0.05,
            electrical_resistance=0.0,
            thermal_conductance=0.0,
        )
        insulated = FourNodeContactThermalParameters(
            cold_face_thermal_capacitance=50.0,
            hot_face_thermal_capacitance=100.0,
            cold_exchanger_thermal_capacitance=50.0,
            hot_exchanger_thermal_capacitance=100.0,
            cold_contact_resistance=0.5,
            hot_contact_resistance=0.25,
            cold_reservoir_conductance=0.0,
            hot_reservoir_conductance=0.0,
        )
        base_inputs = dict(
            cold_face_temperature=300.0,
            hot_face_temperature=300.0,
            cold_exchanger_temperature=300.0,
            hot_exchanger_temperature=300.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )

        positive = four_node_contact_rhs(
            peltier_only,
            insulated,
            current=1.0,
            **base_inputs,
        )
        negative = four_node_contact_rhs(
            peltier_only,
            insulated,
            current=-1.0,
            **base_inputs,
        )

        self.assertAlmostEqual(negative.cold_face, -positive.cold_face)
        self.assertAlmostEqual(negative.hot_face, -positive.hot_face)
        self.assertEqual(positive.cold_exchanger, 0.0)
        self.assertEqual(positive.hot_exchanger, 0.0)
        self.assertEqual(negative.cold_exchanger, 0.0)
        self.assertEqual(negative.hot_exchanger, 0.0)

    def test_invalid_four_node_parameters_are_rejected(self):
        base = dict(
            cold_face_thermal_capacitance=50.0,
            hot_face_thermal_capacitance=100.0,
            cold_exchanger_thermal_capacitance=50.0,
            hot_exchanger_thermal_capacitance=100.0,
            cold_contact_resistance=0.5,
            hot_contact_resistance=0.25,
            cold_reservoir_conductance=2.0,
            hot_reservoir_conductance=4.0,
        )
        invalid_changes = (
            {"cold_face_thermal_capacitance": 0.0},
            {"hot_exchanger_thermal_capacitance": float("nan")},
            {"cold_contact_resistance": 0.0},
            {"hot_contact_resistance": float("inf")},
            {"cold_reservoir_conductance": -1.0},
            {"hot_reservoir_conductance": float("nan")},
        )

        for changes in invalid_changes:
            with self.subTest(changes=changes):
                values = dict(base)
                values.update(changes)
                with self.assertRaises(ValueError):
                    FourNodeContactThermalParameters(**values)

    def test_integrator_preserves_equilibrium_and_shortens_final_step(self):
        trajectory = integrate_four_node_contact(
            self.thermoelectric,
            self.thermal,
            initial_cold_face_temperature=300.0,
            initial_hot_face_temperature=300.0,
            initial_cold_exchanger_temperature=300.0,
            initial_hot_exchanger_temperature=300.0,
            duration=0.25,
            time_step=0.1,
            current=0.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )

        self.assertEqual(trajectory.time, (0.0, 0.1, 0.2, 0.25))
        for history in trajectory[1:]:
            self.assertTrue(all(value == 300.0 for value in history))

    def test_integrator_splits_steps_at_current_transitions(self):
        pulse = PiecewiseConstantCurrent.pulse(
            start_time=1.0,
            end_time=3.0,
            pulse_current=2.0,
        )
        trajectory = integrate_four_node_contact(
            self.thermoelectric,
            self.thermal,
            initial_cold_face_temperature=300.0,
            initial_hot_face_temperature=300.0,
            initial_cold_exchanger_temperature=300.0,
            initial_hot_exchanger_temperature=300.0,
            duration=4.0,
            time_step=3.0,
            current=pulse,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )

        self.assertEqual(trajectory.time, (0.0, 1.0, 3.0, 4.0))

    def test_contact_only_integration_conserves_stored_energy(self):
        no_module_effects = ThermoelectricParameters(
            seebeck_coefficient=0.0,
            electrical_resistance=0.0,
            thermal_conductance=0.0,
        )
        insulated = FourNodeContactThermalParameters(
            cold_face_thermal_capacitance=50.0,
            hot_face_thermal_capacitance=100.0,
            cold_exchanger_thermal_capacitance=50.0,
            hot_exchanger_thermal_capacitance=100.0,
            cold_contact_resistance=0.5,
            hot_contact_resistance=0.25,
            cold_reservoir_conductance=0.0,
            hot_reservoir_conductance=0.0,
        )
        trajectory = integrate_four_node_contact(
            no_module_effects,
            insulated,
            initial_cold_face_temperature=290.0,
            initial_hot_face_temperature=310.0,
            initial_cold_exchanger_temperature=310.0,
            initial_hot_exchanger_temperature=290.0,
            duration=10.0,
            time_step=0.1,
            current=0.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )
        initial_energy = (
            insulated.cold_face_thermal_capacitance
            * trajectory.cold_face[0]
            + insulated.hot_face_thermal_capacitance
            * trajectory.hot_face[0]
            + insulated.cold_exchanger_thermal_capacitance
            * trajectory.cold_exchanger[0]
            + insulated.hot_exchanger_thermal_capacitance
            * trajectory.hot_exchanger[0]
        )

        for values in zip(
            trajectory.cold_face,
            trajectory.hot_face,
            trajectory.cold_exchanger,
            trajectory.hot_exchanger,
        ):
            stored_energy = (
                insulated.cold_face_thermal_capacitance * values[0]
                + insulated.hot_face_thermal_capacitance * values[1]
                + insulated.cold_exchanger_thermal_capacitance * values[2]
                + insulated.hot_exchanger_thermal_capacitance * values[3]
            )
            self.assertAlmostEqual(stored_energy, initial_energy)

    def test_step_refinement_reduces_final_state_difference(self):
        inputs = dict(
            initial_cold_face_temperature=300.0,
            initial_hot_face_temperature=300.0,
            initial_cold_exchanger_temperature=300.0,
            initial_hot_exchanger_temperature=300.0,
            duration=10.0,
            current=1.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )
        coarse = integrate_four_node_contact(
            self.thermoelectric,
            self.thermal,
            time_step=0.2,
            **inputs,
        )
        medium = integrate_four_node_contact(
            self.thermoelectric,
            self.thermal,
            time_step=0.1,
            **inputs,
        )
        fine = integrate_four_node_contact(
            self.thermoelectric,
            self.thermal,
            time_step=0.05,
            **inputs,
        )

        coarse_difference = max(
            abs(coarse[index][-1] - medium[index][-1])
            for index in range(1, 5)
        )
        fine_difference = max(
            abs(medium[index][-1] - fine[index][-1])
            for index in range(1, 5)
        )
        self.assertLess(fine_difference, coarse_difference)

    def test_lower_contact_resistance_approaches_two_node_aggregate(self):
        two_node_thermal = TwoNodeThermalParameters(
            cold_thermal_capacitance=100.0,
            hot_thermal_capacitance=200.0,
            cold_reservoir_conductance=2.0,
            hot_reservoir_conductance=4.0,
        )
        common_inputs = dict(
            duration=5.0,
            time_step=0.005,
            current=1.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )
        reduced = integrate_two_node(
            self.thermoelectric,
            two_node_thermal,
            initial_cold_temperature=300.0,
            initial_hot_temperature=300.0,
            **common_inputs,
        )

        def aggregate_error(contact_resistance):
            parameters = FourNodeContactThermalParameters(
                cold_face_thermal_capacitance=50.0,
                hot_face_thermal_capacitance=100.0,
                cold_exchanger_thermal_capacitance=50.0,
                hot_exchanger_thermal_capacitance=100.0,
                cold_contact_resistance=contact_resistance,
                hot_contact_resistance=contact_resistance,
                cold_reservoir_conductance=2.0,
                hot_reservoir_conductance=4.0,
            )
            trajectory = integrate_four_node_contact(
                self.thermoelectric,
                parameters,
                initial_cold_face_temperature=300.0,
                initial_hot_face_temperature=300.0,
                initial_cold_exchanger_temperature=300.0,
                initial_hot_exchanger_temperature=300.0,
                **common_inputs,
            )
            aggregate_cold = 0.5 * (
                trajectory.cold_face[-1]
                + trajectory.cold_exchanger[-1]
            )
            aggregate_hot = 0.5 * (
                trajectory.hot_face[-1]
                + trajectory.hot_exchanger[-1]
            )
            return max(
                abs(aggregate_cold - reduced.cold[-1]),
                abs(aggregate_hot - reduced.hot[-1]),
            )

        self.assertLess(aggregate_error(0.01), aggregate_error(0.1))


if __name__ == "__main__":
    unittest.main()
