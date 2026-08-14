"""Two-node transient thermal model for ThermoTwin.

The thermoelectric element is quasi-steady. Thermal energy is stored only in
the cold and hot nodes, whose temperatures evolve according to the balances
agreed in Milestone 0.
"""

from dataclasses import dataclass
from typing import NamedTuple

from .thermoelectric import (
    ThermoelectricParameters,
    cold_side_heat,
    hot_side_heat,
)


@dataclass(frozen=True)
class TwoNodeThermalParameters:
    """Thermal properties of the cold and hot lumped nodes.

    Attributes:
        cold_thermal_capacitance: C_c in J/K.
        hot_thermal_capacitance: C_h in J/K.
        cold_reservoir_conductance: G_c in W/K.
        hot_reservoir_conductance: G_h in W/K.

    Reservoir conductances may be zero to represent insulated nodes. Thermal
    capacitances must be strictly positive because the RHS divides by them.
    """

    cold_thermal_capacitance: float
    hot_thermal_capacitance: float
    cold_reservoir_conductance: float
    hot_reservoir_conductance: float

    def __post_init__(self) -> None:
        if self.cold_thermal_capacitance <= 0:
            raise ValueError("cold thermal capacitance must be positive")
        if self.hot_thermal_capacitance <= 0:
            raise ValueError("hot thermal capacitance must be positive")
        if self.cold_reservoir_conductance < 0:
            raise ValueError("cold reservoir conductance cannot be negative")
        if self.hot_reservoir_conductance < 0:
            raise ValueError("hot reservoir conductance cannot be negative")


class TemperatureRates(NamedTuple):
    """Cold and hot temperature rates in K/s, in that order."""

    cold: float
    hot: float


def two_node_rhs(
    thermoelectric_parameters: ThermoelectricParameters,
    thermal_parameters: TwoNodeThermalParameters,
    *,
    cold_temperature: float,
    hot_temperature: float,
    current: float,
    cold_reservoir_temperature: float,
    hot_reservoir_temperature: float,
    cold_external_heat: float = 0.0,
    hot_external_heat: float = 0.0,
) -> TemperatureRates:
    """Return ``(dT_c/dt, dT_h/dt)`` for the two-node model.

    Temperatures are in kelvin, current is in amperes, and external heat inputs
    are in watts. Positive external heat enters its node.

    The implemented balances are

    ``C_c * dT_c/dt = G_c * (T_c_inf - T_c) + q_c_ext - Q_c``

    ``C_h * dT_h/dt = G_h * (T_h_inf - T_h) + q_h_ext + Q_h``.
    """

    cold_heat = cold_side_heat(
        thermoelectric_parameters,
        current,
        hot_temperature,
        cold_temperature,
    )
    hot_heat = hot_side_heat(
        thermoelectric_parameters,
        current,
        hot_temperature,
        cold_temperature,
    )

    cold_reservoir_heat = (
        thermal_parameters.cold_reservoir_conductance
        * (cold_reservoir_temperature - cold_temperature)
    )
    hot_reservoir_heat = (
        thermal_parameters.hot_reservoir_conductance
        * (hot_reservoir_temperature - hot_temperature)
    )

    cold_net_heat = cold_reservoir_heat + cold_external_heat - cold_heat
    hot_net_heat = hot_reservoir_heat + hot_external_heat + hot_heat

    return TemperatureRates(
        cold=cold_net_heat / thermal_parameters.cold_thermal_capacitance,
        hot=hot_net_heat / thermal_parameters.hot_thermal_capacitance,
    )
