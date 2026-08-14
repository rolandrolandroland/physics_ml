import unittest

from thermotwin import (
    ThermoelectricParameters,
    TwoNodeThermalParameters,
    electrical_power,
    two_node_rhs,
)


class TwoNodeTransientTests(unittest.TestCase):
    def setUp(self):
        self.thermoelectric = ThermoelectricParameters(
            seebeck_coefficient=0.05,
            electrical_resistance=2.0,
            thermal_conductance=0.5,
        )
        self.thermal = TwoNodeThermalParameters(
            cold_thermal_capacitance=100.0,
            hot_thermal_capacitance=200.0,
            cold_reservoir_conductance=2.0,
            hot_reservoir_conductance=4.0,
        )

    def test_rhs_matches_the_agreed_node_balances(self):
        rates = two_node_rhs(
            self.thermoelectric,
            self.thermal,
            cold_temperature=300.0,
            hot_temperature=320.0,
            current=3.0,
            cold_reservoir_temperature=295.0,
            hot_reservoir_temperature=300.0,
            cold_external_heat=5.0,
            hot_external_heat=7.0,
        )

        # Q_c = 26 W and Q_h = 47 W for this operating point.
        # Cold net heat: -10 + 5 - 26 = -31 W.
        # Hot net heat: -80 + 7 + 47 = -26 W.
        self.assertAlmostEqual(rates.cold, -31.0 / 100.0)
        self.assertAlmostEqual(rates.hot, -26.0 / 200.0)
        self.assertEqual(tuple(rates), (rates.cold, rates.hot))

    def test_total_stored_energy_rate_matches_all_external_inputs(self):
        cold_temperature = 300.0
        hot_temperature = 320.0
        current = 3.0
        cold_reservoir_temperature = 295.0
        hot_reservoir_temperature = 300.0
        cold_external_heat = 5.0
        hot_external_heat = 7.0

        rates = two_node_rhs(
            self.thermoelectric,
            self.thermal,
            cold_temperature=cold_temperature,
            hot_temperature=hot_temperature,
            current=current,
            cold_reservoir_temperature=cold_reservoir_temperature,
            hot_reservoir_temperature=hot_reservoir_temperature,
            cold_external_heat=cold_external_heat,
            hot_external_heat=hot_external_heat,
        )

        stored_energy_rate = (
            self.thermal.cold_thermal_capacitance * rates.cold
            + self.thermal.hot_thermal_capacitance * rates.hot
        )
        expected_energy_rate = (
            self.thermal.cold_reservoir_conductance
            * (cold_reservoir_temperature - cold_temperature)
            + self.thermal.hot_reservoir_conductance
            * (hot_reservoir_temperature - hot_temperature)
            + cold_external_heat
            + hot_external_heat
            + electrical_power(
                self.thermoelectric,
                current,
                hot_temperature,
                cold_temperature,
            )
        )
        self.assertAlmostEqual(stored_energy_rate, expected_energy_rate)

    def test_equal_temperatures_with_no_current_or_load_are_equilibrium(self):
        rates = two_node_rhs(
            self.thermoelectric,
            self.thermal,
            cold_temperature=300.0,
            hot_temperature=300.0,
            current=0.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )

        self.assertEqual(rates.cold, 0.0)
        self.assertEqual(rates.hot, 0.0)

    def test_passive_module_conduction_warms_cold_and_cools_hot_node(self):
        insulated_nodes = TwoNodeThermalParameters(
            cold_thermal_capacitance=100.0,
            hot_thermal_capacitance=200.0,
            cold_reservoir_conductance=0.0,
            hot_reservoir_conductance=0.0,
        )
        rates = two_node_rhs(
            self.thermoelectric,
            insulated_nodes,
            cold_temperature=300.0,
            hot_temperature=320.0,
            current=0.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=320.0,
        )

        self.assertGreater(rates.cold, 0.0)
        self.assertLess(rates.hot, 0.0)
        self.assertAlmostEqual(
            insulated_nodes.cold_thermal_capacitance * rates.cold
            + insulated_nodes.hot_thermal_capacitance * rates.hot,
            0.0,
        )

    def test_positive_refrigeration_current_cools_cold_and_heats_hot_node(self):
        insulated_nodes = TwoNodeThermalParameters(
            cold_thermal_capacitance=100.0,
            hot_thermal_capacitance=200.0,
            cold_reservoir_conductance=0.0,
            hot_reservoir_conductance=0.0,
        )
        rates = two_node_rhs(
            self.thermoelectric,
            insulated_nodes,
            cold_temperature=300.0,
            hot_temperature=300.0,
            current=1.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
        )

        self.assertLess(rates.cold, 0.0)
        self.assertGreater(rates.hot, 0.0)

    def test_doubling_capacitance_halves_rate_for_same_net_heat(self):
        base = TwoNodeThermalParameters(
            cold_thermal_capacitance=100.0,
            hot_thermal_capacitance=200.0,
            cold_reservoir_conductance=0.0,
            hot_reservoir_conductance=0.0,
        )
        doubled = TwoNodeThermalParameters(
            cold_thermal_capacitance=200.0,
            hot_thermal_capacitance=400.0,
            cold_reservoir_conductance=0.0,
            hot_reservoir_conductance=0.0,
        )
        inputs = dict(
            cold_temperature=300.0,
            hot_temperature=300.0,
            current=0.0,
            cold_reservoir_temperature=300.0,
            hot_reservoir_temperature=300.0,
            cold_external_heat=10.0,
            hot_external_heat=20.0,
        )

        base_rates = two_node_rhs(
            self.thermoelectric, base, **inputs
        )
        doubled_rates = two_node_rhs(
            self.thermoelectric, doubled, **inputs
        )

        self.assertAlmostEqual(doubled_rates.cold, 0.5 * base_rates.cold)
        self.assertAlmostEqual(doubled_rates.hot, 0.5 * base_rates.hot)

    def test_invalid_thermal_parameters_are_rejected(self):
        invalid_cases = (
            dict(
                cold_thermal_capacitance=0.0,
                hot_thermal_capacitance=1.0,
                cold_reservoir_conductance=0.0,
                hot_reservoir_conductance=0.0,
            ),
            dict(
                cold_thermal_capacitance=1.0,
                hot_thermal_capacitance=-1.0,
                cold_reservoir_conductance=0.0,
                hot_reservoir_conductance=0.0,
            ),
            dict(
                cold_thermal_capacitance=1.0,
                hot_thermal_capacitance=1.0,
                cold_reservoir_conductance=-1.0,
                hot_reservoir_conductance=0.0,
            ),
            dict(
                cold_thermal_capacitance=1.0,
                hot_thermal_capacitance=1.0,
                cold_reservoir_conductance=0.0,
                hot_reservoir_conductance=-1.0,
            ),
        )

        for values in invalid_cases:
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    TwoNodeThermalParameters(**values)


if __name__ == "__main__":
    unittest.main()
