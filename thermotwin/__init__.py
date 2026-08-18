"""ThermoTwin physics models."""

from .controls import PiecewiseConstantCurrent

from .contact_transient import (
    FourNodeContactTemperatureRates,
    FourNodeContactTemperatureTrajectory,
    FourNodeContactThermalParameters,
    four_node_contact_rhs,
    integrate_four_node_contact,
    thermal_contact_heat,
)

from .contact_diagnostics import (
    ContactTrajectoryDiagnostics,
    evaluate_contact_trajectory,
)

from .contact_experiments import (
    ContactExperimentResult,
    FourNodeContactExperiment,
    constant_current_contact_reference_experiment,
    run_four_node_contact_experiment,
)

from .transient import (
    SteadyStateTemperatures,
    TemperatureRates,
    TemperatureTrajectory,
    TwoNodeThermalParameters,
    integrate_two_node,
    two_node_rhs,
    two_node_steady_state,
)

from .thermoelectric import (
    ThermoelectricParameters,
    coefficient_of_performance,
    cold_side_heat,
    conductive_heat_leak,
    electrical_power,
    hot_side_heat,
    joule_heating,
    peltier_heat,
    voltage,
)

from .diagnostics import TrajectoryDiagnostics, evaluate_trajectory

from .experiments import (
    ExperimentResult,
    TwoNodeExperiment,
    constant_current_reference_experiment,
    run_two_node_experiment,
)

from .virtual_test_stand import (
    IdealTemperatureSensor,
    IdealVirtualTestStand,
    ObservationDataset,
    TemperatureObservation,
    TemperatureSensorLocation,
    ideal_four_sensor_test_stand,
    observe_contact_trajectory,
    regular_measurement_times,
    run_ideal_contact_reference_test_stand,
)

from .measurement_noise import (
    GaussianTemperatureNoise,
    TemperatureNoiseResult,
    apply_gaussian_temperature_noise,
    reference_gaussian_temperature_noise,
    run_noisy_contact_reference_test_stand,
)

__all__ = [
    "ContactExperimentResult",
    "ContactTrajectoryDiagnostics",
    "FourNodeContactExperiment",
    "FourNodeContactTemperatureRates",
    "FourNodeContactTemperatureTrajectory",
    "FourNodeContactThermalParameters",
    "GaussianTemperatureNoise",
    "IdealTemperatureSensor",
    "IdealVirtualTestStand",
    "ObservationDataset",
    "SteadyStateTemperatures",
    "TemperatureRates",
    "TemperatureObservation",
    "TemperatureNoiseResult",
    "TemperatureSensorLocation",
    "TemperatureTrajectory",
    "ThermoelectricParameters",
    "TrajectoryDiagnostics",
    "ExperimentResult",
    "TwoNodeExperiment",
    "TwoNodeThermalParameters",
    "PiecewiseConstantCurrent",
    "coefficient_of_performance",
    "apply_gaussian_temperature_noise",
    "cold_side_heat",
    "constant_current_contact_reference_experiment",
    "constant_current_reference_experiment",
    "conductive_heat_leak",
    "electrical_power",
    "evaluate_trajectory",
    "evaluate_contact_trajectory",
    "four_node_contact_rhs",
    "hot_side_heat",
    "integrate_four_node_contact",
    "integrate_two_node",
    "ideal_four_sensor_test_stand",
    "joule_heating",
    "peltier_heat",
    "observe_contact_trajectory",
    "regular_measurement_times",
    "reference_gaussian_temperature_noise",
    "run_two_node_experiment",
    "run_four_node_contact_experiment",
    "run_ideal_contact_reference_test_stand",
    "run_noisy_contact_reference_test_stand",
    "thermal_contact_heat",
    "two_node_rhs",
    "two_node_steady_state",
    "voltage",
]
