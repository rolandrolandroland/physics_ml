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

__all__ = [
    "ContactExperimentResult",
    "ContactTrajectoryDiagnostics",
    "FourNodeContactExperiment",
    "FourNodeContactTemperatureRates",
    "FourNodeContactTemperatureTrajectory",
    "FourNodeContactThermalParameters",
    "SteadyStateTemperatures",
    "TemperatureRates",
    "TemperatureTrajectory",
    "ThermoelectricParameters",
    "TrajectoryDiagnostics",
    "ExperimentResult",
    "TwoNodeExperiment",
    "TwoNodeThermalParameters",
    "PiecewiseConstantCurrent",
    "coefficient_of_performance",
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
    "joule_heating",
    "peltier_heat",
    "run_two_node_experiment",
    "run_four_node_contact_experiment",
    "thermal_contact_heat",
    "two_node_rhs",
    "two_node_steady_state",
    "voltage",
]
