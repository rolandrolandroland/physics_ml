"""ThermoTwin physics models."""

from .controls import PiecewiseConstantCurrent

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
    "constant_current_reference_experiment",
    "conductive_heat_leak",
    "electrical_power",
    "evaluate_trajectory",
    "hot_side_heat",
    "integrate_two_node",
    "joule_heating",
    "peltier_heat",
    "run_two_node_experiment",
    "two_node_rhs",
    "two_node_steady_state",
    "voltage",
]
