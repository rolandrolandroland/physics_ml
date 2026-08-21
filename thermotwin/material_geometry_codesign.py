"""Cost-aware virtual co-design of TEC materials, geometry, and heat rejection.

This module connects same-row public material-property records to the existing
contact-aware steady thermoelectric model.  It supplies three CPU-first virtual
experiments:

1. a 24-design space-filling screen;
2. Gaussian-process Bayesian optimization versus equal-budget random search;
3. fixed-control robustness checks for as-built property and interface spread.

The public data are real literature-derived material records.  Geometry,
assembly parasitics, converter performance, cost index, application limits,
and manufacturing uncertainty are explicit virtual-study assumptions.  The
result is therefore a method demonstration, not a hardware design release.
"""

from dataclasses import dataclass, replace
import math
import random
from typing import NamedTuple, Optional, Sequence, Tuple

from .contact_transient import (
    FourNodeContactSteadyState,
    FourNodeContactThermalParameters,
    four_node_contact_steady_state_from_current_moments,
)
from .material_catalog import (
    MaterialSample,
    N_TYPE_SAMPLES,
    P_TYPE_SAMPLES,
)
from .pwm_power_electronics import (
    AveragedThermoelectricRates,
    CurrentMoments,
    averaged_thermoelectric_rates,
    smoothed_pwm_current_moments,
)
from .small_matrix import inverse_and_determinant
from .thermoelectric import ThermoelectricParameters


CURRENT_DENSITY_BINDING_UTILIZATION = 0.995


@dataclass(frozen=True)
class ModuleGeometry:
    """Repeated p/n-leg geometry for one idealized thermoelectric module."""

    couple_count: int
    leg_length: float
    leg_area: float
    packing_fraction: float = 0.65

    def __post_init__(self) -> None:
        if isinstance(self.couple_count, bool) or self.couple_count <= 0:
            raise ValueError("couple count must be a positive integer")
        if int(self.couple_count) != self.couple_count:
            raise ValueError("couple count must be an integer")
        for name, value in (
            ("leg length", self.leg_length),
            ("leg area", self.leg_area),
            ("packing fraction", self.packing_fraction),
        ):
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.packing_fraction > 1.0:
            raise ValueError("packing fraction cannot exceed one")

    @property
    def active_material_volume(self) -> float:
        """Return total p-plus-n leg volume in cubic metres."""

        return 2.0 * self.couple_count * self.leg_area * self.leg_length

    @property
    def estimated_footprint_area(self) -> float:
        """Return leg-area-based module footprint estimate in square metres."""

        return 2.0 * self.couple_count * self.leg_area / self.packing_fraction


@dataclass(frozen=True)
class ModuleAssemblyAssumptions:
    """Documented non-material contributions used in the virtual campaign."""

    specific_electrical_contact_resistivity: float = 2.0e-10
    parasitic_thermal_conductance: float = 0.04
    pwm_ripple_peak_to_peak_fraction: float = 0.10
    converter_efficiency: float = 0.95
    fixed_converter_loss: float = 0.05
    maximum_current_density: float = 1.0e6
    maximum_peak_voltage: float = 12.0

    def __post_init__(self) -> None:
        positive = (
            ("maximum current density", self.maximum_current_density),
            ("maximum peak voltage", self.maximum_peak_voltage),
        )
        for name, value in positive:
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        nonnegative = (
            (
                "specific electrical contact resistivity",
                self.specific_electrical_contact_resistivity,
            ),
            ("parasitic thermal conductance", self.parasitic_thermal_conductance),
            ("PWM ripple fraction", self.pwm_ripple_peak_to_peak_fraction),
            ("fixed converter loss", self.fixed_converter_loss),
        )
        for name, value in nonnegative:
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and nonnegative")
        if not 0.0 < self.converter_efficiency <= 1.0:
            raise ValueError("converter efficiency must lie in (0, 1]")


@dataclass(frozen=True)
class PrototypeDesign:
    """One virtual material, geometry, contact, and exchanger design."""

    design_id: str
    p_sample_index: int
    n_sample_index: int
    geometry: ModuleGeometry
    symmetric_contact_resistance: float
    cold_exchanger_conductance: float
    hot_exchanger_conductance: float

    def __post_init__(self) -> None:
        if not self.design_id:
            raise ValueError("design ID must be nonempty")
        if not 0 <= self.p_sample_index < len(P_TYPE_SAMPLES):
            raise ValueError("p-sample index is outside the curated catalog")
        if not 0 <= self.n_sample_index < len(N_TYPE_SAMPLES):
            raise ValueError("n-sample index is outside the curated catalog")
        for name, value in (
            ("contact resistance", self.symmetric_contact_resistance),
            ("cold exchanger conductance", self.cold_exchanger_conductance),
            ("hot exchanger conductance", self.hot_exchanger_conductance),
        ):
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")

    @property
    def p_material(self) -> MaterialSample:
        return P_TYPE_SAMPLES[self.p_sample_index]

    @property
    def n_material(self) -> MaterialSample:
        return N_TYPE_SAMPLES[self.n_sample_index]


@dataclass(frozen=True)
class PropertyMultipliers:
    """Dimensionless as-built multipliers used by the robustness experiment."""

    p_seebeck: float = 1.0
    n_seebeck: float = 1.0
    p_electrical_conductivity: float = 1.0
    n_electrical_conductivity: float = 1.0
    p_thermal_conductivity: float = 1.0
    n_thermal_conductivity: float = 1.0

    def __post_init__(self) -> None:
        if any(
            not math.isfinite(value) or value <= 0.0
            for value in self
        ):
            raise ValueError("all material-property multipliers must be positive")

    def __iter__(self):
        return iter(
            (
                self.p_seebeck,
                self.n_seebeck,
                self.p_electrical_conductivity,
                self.n_electrical_conductivity,
                self.p_thermal_conductivity,
                self.n_thermal_conductivity,
            )
        )


@dataclass(frozen=True)
class ApplicationSpecification:
    """Cooling requirement and scalar decision objective for one use case."""

    name: str
    label: str
    external_temperature_lift: float
    minimum_cooling_rate: float
    minimum_wall_cop: float
    maximum_supply_power: float
    objective: str

    def __post_init__(self) -> None:
        if not self.name or not self.label:
            raise ValueError("application name and label must be nonempty")
        if self.objective not in {"efficiency", "balanced", "capacity"}:
            raise ValueError("unknown application objective")
        for name, value, allow_zero in (
            ("temperature lift", self.external_temperature_lift, True),
            ("minimum cooling rate", self.minimum_cooling_rate, True),
            ("minimum wall COP", self.minimum_wall_cop, True),
            ("maximum supply power", self.maximum_supply_power, False),
        ):
            if not math.isfinite(value) or value < 0.0 or (not allow_zero and value == 0.0):
                raise ValueError(f"{name} is invalid")


APPLICATION_SPECIFICATIONS: Tuple[ApplicationSpecification, ...] = (
    ApplicationSpecification(
        "low_lift_efficiency",
        "10 K efficiency-first",
        10.0,
        2.5,
        0.75,
        25.0,
        "efficiency",
    ),
    ApplicationSpecification(
        "high_lift_balanced",
        "25 K balanced",
        25.0,
        0.75,
        0.15,
        30.0,
        "balanced",
    ),
    ApplicationSpecification(
        "capacity_first",
        "10 K capacity-first",
        10.0,
        4.0,
        0.60,
        30.0,
        "capacity",
    ),
)


class DesignOperatingPoint(NamedTuple):
    """One design at its selected mean-current operating point."""

    design: PrototypeDesign
    application: ApplicationSpecification
    thermoelectric_parameters: ThermoelectricParameters
    bulk_leg_electrical_resistance: float
    electrical_contact_resistance: float
    mean_current: float
    peak_current: float
    cold_face_temperature: float
    hot_face_temperature: float
    cold_exchanger_temperature: float
    hot_exchanger_temperature: float
    delivered_cooling_rate: float
    delivered_heating_rate: float
    module_electrical_power: float
    supply_electrical_power: float
    wall_cooling_cop: Optional[float]
    heat_flux: float
    prototype_cost_index: float
    peak_voltage: float
    peak_current_density: float
    current_density_utilization: float
    current_density_constraint_binding: bool
    feasible: bool
    utility: float


class InitialDesignSummary(NamedTuple):
    application: ApplicationSpecification
    evaluations: Tuple[DesignOperatingPoint, ...]
    feasible_count: int
    best: DesignOperatingPoint


class BayesianOptimizationResult(NamedTuple):
    application: ApplicationSpecification
    initial_evaluations: Tuple[DesignOperatingPoint, ...]
    acquired_evaluations: Tuple[DesignOperatingPoint, ...]
    best_utility_history: Tuple[float, ...]
    random_median_history: Tuple[float, ...]
    random_lower_history: Tuple[float, ...]
    random_upper_history: Tuple[float, ...]
    selected: DesignOperatingPoint
    oracle_best: DesignOperatingPoint


class RobustnessResult(NamedTuple):
    application: ApplicationSpecification
    nominal: DesignOperatingPoint
    trial_count: int
    feasible_fraction: float
    cooling_rate_quantiles: Tuple[float, float, float]
    wall_cop_quantiles: Tuple[float, float, float]
    hot_face_temperature_quantiles: Tuple[float, float, float]


@dataclass(frozen=True)
class CodesignCampaignConfig:
    initial_design_count: int = 24
    candidate_design_count: int = 180
    bayesian_iterations: int = 12
    random_search_repetitions: int = 25
    robustness_trials: int = 300
    seed: int = 20260821
    current_grid_size: int = 28
    assembly: ModuleAssemblyAssumptions = ModuleAssemblyAssumptions()

    def __post_init__(self) -> None:
        for name, value in (
            ("initial design count", self.initial_design_count),
            ("candidate design count", self.candidate_design_count),
            ("Bayesian iterations", self.bayesian_iterations),
            ("random repetitions", self.random_search_repetitions),
            ("robustness trials", self.robustness_trials),
            ("current grid size", self.current_grid_size),
        ):
            if isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.bayesian_iterations > self.candidate_design_count:
            raise ValueError("Bayesian iterations exceed candidate count")


class CodesignCampaignResult(NamedTuple):
    config: CodesignCampaignConfig
    initial_designs: Tuple[PrototypeDesign, ...]
    candidate_designs: Tuple[PrototypeDesign, ...]
    initial_summaries: Tuple[InitialDesignSummary, ...]
    bayesian_results: Tuple[BayesianOptimizationResult, ...]
    robustness_results: Tuple[RobustnessResult, ...]


class ModuleElectricalResistanceComponents(NamedTuple):
    """Bulk-leg and areal-contact contributions to module resistance."""

    bulk_leg_resistance: float
    electrical_contact_resistance: float
    total_resistance: float
    contact_fraction: float


def module_electrical_resistance_components(
    p_material: MaterialSample,
    n_material: MaterialSample,
    geometry: ModuleGeometry,
    *,
    assembly: ModuleAssemblyAssumptions = ModuleAssemblyAssumptions(),
    multipliers: PropertyMultipliers = PropertyMultipliers(),
) -> ModuleElectricalResistanceComponents:
    """Return bulk and metal/thermoelectric interface resistance.

    Each p and n leg has two metal/thermoelectric interfaces. With one
    symmetric specific contact resistivity ``rho_c`` per interface, the four
    interfaces in each series p/n couple contribute ``4*rho_c/A``. Repeating
    ``N`` couples in electrical series gives ``4*N*rho_c/A``. Unlike bulk leg
    resistance, this areal contact term is independent of leg length.
    """

    if p_material.carrier_type != "p" or n_material.carrier_type != "n":
        raise ValueError("module requires one p-type and one n-type material")
    p_resistivity = 1.0 / (
        p_material.electrical_conductivity
        * multipliers.p_electrical_conductivity
    )
    n_resistivity = 1.0 / (
        n_material.electrical_conductivity
        * multipliers.n_electrical_conductivity
    )
    bulk_leg_resistance = (
        geometry.couple_count
        * geometry.leg_length
        / geometry.leg_area
        * (p_resistivity + n_resistivity)
    )
    electrical_contact_resistance = (
        4.0
        * geometry.couple_count
        * assembly.specific_electrical_contact_resistivity
        / geometry.leg_area
    )
    total_resistance = bulk_leg_resistance + electrical_contact_resistance
    contact_fraction = (
        electrical_contact_resistance / total_resistance
        if total_resistance > 0.0
        else 0.0
    )
    return ModuleElectricalResistanceComponents(
        bulk_leg_resistance,
        electrical_contact_resistance,
        total_resistance,
        contact_fraction,
    )


def module_thermoelectric_parameters(
    p_material: MaterialSample,
    n_material: MaterialSample,
    geometry: ModuleGeometry,
    *,
    assembly: ModuleAssemblyAssumptions = ModuleAssemblyAssumptions(),
    multipliers: PropertyMultipliers = PropertyMultipliers(),
) -> ThermoelectricParameters:
    """Scale material properties into constant module alpha, R, and K.

    The p and n legs are thermally parallel and electrically series within a
    couple.  Couples are then electrically series and thermally parallel.
    """

    alpha_pair = (
        p_material.seebeck_coefficient * multipliers.p_seebeck
        - n_material.seebeck_coefficient * multipliers.n_seebeck
    )
    resistance = module_electrical_resistance_components(
        p_material,
        n_material,
        geometry,
        assembly=assembly,
        multipliers=multipliers,
    )
    leg_conductance = (
        geometry.couple_count
        * geometry.leg_area
        / geometry.leg_length
        * (
            p_material.thermal_conductivity
            * multipliers.p_thermal_conductivity
            + n_material.thermal_conductivity
            * multipliers.n_thermal_conductivity
        )
    )
    return ThermoelectricParameters(
        seebeck_coefficient=geometry.couple_count * alpha_pair,
        electrical_resistance=resistance.total_resistance,
        thermal_conductance=(
            leg_conductance + assembly.parasitic_thermal_conductance
        ),
    )


def prototype_cost_index(design: PrototypeDesign) -> float:
    """Return an explicit relative build-burden proxy, not a dollar estimate."""

    baseline_volume = 2.0 * 120.0 * 1.6e-6 * 1.5e-3
    material_volume_term = design.geometry.active_material_volume / baseline_volume
    assembly_term = design.geometry.couple_count / 120.0
    cold_exchanger_term = design.cold_exchanger_conductance / 2.5
    hot_exchanger_term = design.hot_exchanger_conductance / 5.0
    return (
        0.40 * material_volume_term
        + 0.20 * assembly_term
        + 0.20 * cold_exchanger_term
        + 0.20 * hot_exchanger_term
    )


def averaged_contact_steady_state_for_parameters(
    thermoelectric_parameters: ThermoelectricParameters,
    thermal_parameters: FourNodeContactThermalParameters,
    current: CurrentMoments,
    *,
    cold_reservoir_temperature: float,
    hot_reservoir_temperature: float,
) -> FourNodeContactSteadyState:
    """Delegate arbitrary module/current moments to the shared steady kernel."""

    return four_node_contact_steady_state_from_current_moments(
        thermoelectric_parameters,
        thermal_parameters,
        mean_current=current.mean_current,
        mean_square_current=current.mean_square_current,
        cold_reservoir_temperature=cold_reservoir_temperature,
        hot_reservoir_temperature=hot_reservoir_temperature,
    )


def _application_utility(
    application: ApplicationSpecification,
    *,
    cooling_rate: float,
    wall_cop: Optional[float],
    heat_flux: float,
    cost_index: float,
    supply_power: float,
    peak_voltage: float,
    maximum_peak_voltage: float,
) -> Tuple[bool, float]:
    cop_value = wall_cop if wall_cop is not None else 0.0
    violations = (
        max(0.0, application.minimum_cooling_rate - cooling_rate)
        / max(application.minimum_cooling_rate, 1.0),
        max(0.0, application.minimum_wall_cop - cop_value)
        / max(application.minimum_wall_cop, 1.0),
        max(0.0, supply_power - application.maximum_supply_power)
        / application.maximum_supply_power,
        max(0.0, peak_voltage - maximum_peak_voltage) / maximum_peak_voltage,
    )
    feasible = not any(value > 0.0 for value in violations)
    if not feasible:
        return False, -1.0 - sum(violations)
    if application.objective == "efficiency":
        utility = cop_value / math.sqrt(cost_index)
    elif application.objective == "balanced":
        utility = cooling_rate * cop_value / cost_index
    else:
        utility = heat_flux * math.sqrt(cop_value) / math.sqrt(cost_index)
    return True, utility


def evaluate_design_current(
    design: PrototypeDesign,
    application: ApplicationSpecification,
    mean_current: float,
    *,
    assembly: ModuleAssemblyAssumptions = ModuleAssemblyAssumptions(),
    multipliers: PropertyMultipliers = PropertyMultipliers(),
    electrical_contact_resistivity_multiplier: float = 1.0,
    contact_multiplier: float = 1.0,
    cold_exchanger_multiplier: float = 1.0,
    hot_exchanger_multiplier: float = 1.0,
    converter_efficiency: Optional[float] = None,
) -> DesignOperatingPoint:
    """Evaluate one fixed mean-current, smoothed-PWM operating point."""

    if not math.isfinite(mean_current) or mean_current <= 0.0:
        raise ValueError("mean current must be finite and positive")
    if any(
        not math.isfinite(value) or value <= 0.0
        for value in (
            electrical_contact_resistivity_multiplier,
            contact_multiplier,
            cold_exchanger_multiplier,
            hot_exchanger_multiplier,
        )
    ):
        raise ValueError("interface multipliers must be finite and positive")
    efficiency = (
        assembly.converter_efficiency
        if converter_efficiency is None
        else converter_efficiency
    )
    if not math.isfinite(efficiency) or not 0.0 < efficiency <= 1.0:
        raise ValueError("converter efficiency must lie in (0, 1]")
    effective_assembly = replace(
        assembly,
        specific_electrical_contact_resistivity=(
            assembly.specific_electrical_contact_resistivity
            * electrical_contact_resistivity_multiplier
        ),
    )
    current = smoothed_pwm_current_moments(
        mean_current,
        effective_assembly.pwm_ripple_peak_to_peak_fraction,
    )
    resistance = module_electrical_resistance_components(
        design.p_material,
        design.n_material,
        design.geometry,
        assembly=effective_assembly,
        multipliers=multipliers,
    )
    parameters = module_thermoelectric_parameters(
        design.p_material,
        design.n_material,
        design.geometry,
        assembly=effective_assembly,
        multipliers=multipliers,
    )
    thermal = FourNodeContactThermalParameters(
        cold_face_thermal_capacitance=1.0,
        hot_face_thermal_capacitance=1.0,
        cold_exchanger_thermal_capacitance=1.0,
        hot_exchanger_thermal_capacitance=1.0,
        cold_contact_resistance=(
            design.symmetric_contact_resistance * contact_multiplier
        ),
        hot_contact_resistance=(
            design.symmetric_contact_resistance * contact_multiplier
        ),
        cold_reservoir_conductance=(
            design.cold_exchanger_conductance * cold_exchanger_multiplier
        ),
        hot_reservoir_conductance=(
            design.hot_exchanger_conductance * hot_exchanger_multiplier
        ),
    )
    half_lift = 0.5 * application.external_temperature_lift
    cold_reservoir = 300.0 - half_lift
    hot_reservoir = 300.0 + half_lift
    state = averaged_contact_steady_state_for_parameters(
        parameters,
        thermal,
        current,
        cold_reservoir_temperature=cold_reservoir,
        hot_reservoir_temperature=hot_reservoir,
    )
    rates: AveragedThermoelectricRates = averaged_thermoelectric_rates(
        seebeck_coefficient=parameters.seebeck_coefficient,
        electrical_resistance=parameters.electrical_resistance,
        thermal_conductance=parameters.thermal_conductance,
        current=current,
        hot_temperature=state.hot_face,
        cold_temperature=state.cold_face,
    )
    delivered_cooling = thermal.cold_reservoir_conductance * (
        cold_reservoir - state.cold_exchanger
    )
    delivered_heating = thermal.hot_reservoir_conductance * (
        state.hot_exchanger - hot_reservoir
    )
    if not math.isclose(delivered_cooling, rates.cold_heat, abs_tol=1e-9):
        raise RuntimeError("cold-side steady energy balance did not close")
    if not math.isclose(delivered_heating, rates.hot_heat, abs_tol=1e-9):
        raise RuntimeError("hot-side steady energy balance did not close")
    supply_power = (
        rates.module_electrical_power / efficiency
        + effective_assembly.fixed_converter_loss
    )
    wall_cop = (
        delivered_cooling / supply_power
        if delivered_cooling > 0.0 and supply_power > 0.0
        else None
    )
    footprint = design.geometry.estimated_footprint_area
    heat_flux = delivered_cooling / (footprint * 1.0e4)
    cost_index = prototype_cost_index(design)
    peak_voltage = (
        parameters.seebeck_coefficient * (state.hot_face - state.cold_face)
        + current.peak_current * parameters.electrical_resistance
    )
    peak_current_density = current.peak_current / design.geometry.leg_area
    current_density_utilization = (
        peak_current_density / effective_assembly.maximum_current_density
    )
    current_density_ok = (
        current_density_utilization <= 1.0 + 1e-12
    )
    current_density_binding = (
        current_density_utilization >= CURRENT_DENSITY_BINDING_UTILIZATION
    )
    feasible, utility = _application_utility(
        application,
        cooling_rate=delivered_cooling,
        wall_cop=wall_cop,
        heat_flux=heat_flux,
        cost_index=cost_index,
        supply_power=supply_power,
        peak_voltage=peak_voltage,
        maximum_peak_voltage=effective_assembly.maximum_peak_voltage,
    )
    if not current_density_ok:
        feasible = False
        excess = (
            current_density_utilization - 1.0
        )
        utility = min(utility, -1.0 - excess)
    return DesignOperatingPoint(
        design,
        application,
        parameters,
        resistance.bulk_leg_resistance,
        resistance.electrical_contact_resistance,
        current.mean_current,
        current.peak_current,
        state.cold_face,
        state.hot_face,
        state.cold_exchanger,
        state.hot_exchanger,
        delivered_cooling,
        delivered_heating,
        rates.module_electrical_power,
        supply_power,
        wall_cop,
        heat_flux,
        cost_index,
        peak_voltage,
        peak_current_density,
        current_density_utilization,
        current_density_binding,
        feasible,
        utility,
    )


def optimize_design_current(
    design: PrototypeDesign,
    application: ApplicationSpecification,
    *,
    grid_size: int = 28,
    assembly: ModuleAssemblyAssumptions = ModuleAssemblyAssumptions(),
) -> DesignOperatingPoint:
    """Select the best feasible grid current, or least-violating point."""

    if isinstance(grid_size, bool) or grid_size < 2:
        raise ValueError("current grid size must be at least two")
    maximum_mean_current = (
        assembly.maximum_current_density
        * design.geometry.leg_area
        / (1.0 + 0.5 * assembly.pwm_ripple_peak_to_peak_fraction)
    )
    minimum_current = min(0.05, 0.05 * maximum_mean_current)
    currents = tuple(
        minimum_current
        + (maximum_mean_current - minimum_current) * index / (grid_size - 1)
        for index in range(grid_size)
    )
    points = tuple(
        evaluate_design_current(
            design,
            application,
            current,
            assembly=assembly,
        )
        for current in currents
    )
    return max(points, key=lambda point: point.utility)


def latin_hypercube(count: int, dimensions: int, seed: int) -> Tuple[Tuple[float, ...], ...]:
    """Return a reproducible unit-cube Latin hypercube without dependencies."""

    if isinstance(count, bool) or not isinstance(count, int) or count <= 0:
        raise ValueError("count must be a positive integer")
    if (
        isinstance(dimensions, bool)
        or not isinstance(dimensions, int)
        or dimensions <= 0
    ):
        raise ValueError("dimensions must be a positive integer")
    generator = random.Random(seed)
    columns = []
    for _ in range(dimensions):
        strata = list(range(count))
        generator.shuffle(strata)
        columns.append(
            tuple((stratum + generator.random()) / count for stratum in strata)
        )
    return tuple(
        tuple(columns[dimension][row] for dimension in range(dimensions))
        for row in range(count)
    )


def generate_space_filling_designs(
    count: int,
    *,
    seed: int,
    prefix: str,
) -> Tuple[PrototypeDesign, ...]:
    """Map an eight-dimensional Latin hypercube into the design envelope."""

    rows = latin_hypercube(count, 8, seed)
    designs = []
    for index, row in enumerate(rows):
        p_index = min(int(row[0] * len(P_TYPE_SAMPLES)), len(P_TYPE_SAMPLES) - 1)
        n_index = min(int(row[1] * len(N_TYPE_SAMPLES)), len(N_TYPE_SAMPLES) - 1)
        couple_count = int(round(80.0 + 80.0 * row[2]))
        leg_length = (0.8 + 1.6 * row[3]) * 1.0e-3
        leg_area = (0.8 + 1.6 * row[4]) * 1.0e-6
        contact_resistance = 0.10 + 0.40 * row[5]
        cold_conductance = 1.5 + 3.5 * row[6]
        hot_conductance = 3.0 + 5.0 * row[7]
        designs.append(
            PrototypeDesign(
                f"{prefix}-{index + 1:03d}",
                p_index,
                n_index,
                ModuleGeometry(couple_count, leg_length, leg_area),
                contact_resistance,
                cold_conductance,
                hot_conductance,
            )
        )
    return tuple(designs)


def design_features(design: PrototypeDesign) -> Tuple[float, ...]:
    """Return normalized continuous features plus one-hot material choices."""

    continuous = (
        (design.geometry.couple_count - 80.0) / 80.0,
        (design.geometry.leg_length / 1.0e-3 - 0.8) / 1.6,
        (design.geometry.leg_area / 1.0e-6 - 0.8) / 1.6,
        (design.symmetric_contact_resistance - 0.10) / 0.40,
        (design.cold_exchanger_conductance - 1.5) / 3.5,
        (design.hot_exchanger_conductance - 3.0) / 5.0,
    )
    p_one_hot = tuple(
        1.0 if index == design.p_sample_index else 0.0
        for index in range(len(P_TYPE_SAMPLES))
    )
    n_one_hot = tuple(
        1.0 if index == design.n_sample_index else 0.0
        for index in range(len(N_TYPE_SAMPLES))
    )
    return continuous + p_one_hot + n_one_hot


def _kernel(left: Sequence[float], right: Sequence[float], length_scale: float = 1.4) -> float:
    squared_distance = sum((a - b) ** 2 for a, b in zip(left, right))
    return math.exp(-0.5 * squared_distance / length_scale**2)


def gaussian_process_predict(
    observed_features: Sequence[Sequence[float]],
    observed_values: Sequence[float],
    query_features: Sequence[float],
    *,
    nugget: float = 1.0e-5,
) -> Tuple[float, float]:
    """Return GP posterior mean and standard deviation for one query."""

    features = tuple(tuple(row) for row in observed_features)
    values = tuple(float(value) for value in observed_values)
    if not features or len(features) != len(values):
        raise ValueError("GP observations must be nonempty and aligned")
    if any(len(row) != len(features[0]) for row in features):
        raise ValueError("GP feature rows must have equal width")
    if len(query_features) != len(features[0]):
        raise ValueError("query feature width does not match observations")
    if not math.isfinite(nugget) or nugget <= 0.0:
        raise ValueError("GP nugget must be positive and finite")
    mean_value = sum(values) / len(values)
    variance_value = sum((value - mean_value) ** 2 for value in values) / len(values)
    scale_value = max(math.sqrt(variance_value), 1.0e-9)
    standardized = tuple((value - mean_value) / scale_value for value in values)
    covariance = tuple(
        tuple(
            _kernel(left, right) + (nugget if i == j else 0.0)
            for j, right in enumerate(features)
        )
        for i, left in enumerate(features)
    )
    inverse, _ = inverse_and_determinant(covariance)
    alpha = tuple(
        sum(coefficient * value for coefficient, value in zip(row, standardized))
        for row in inverse
    )
    query_covariance = tuple(_kernel(query_features, row) for row in features)
    standardized_mean = sum(a * b for a, b in zip(query_covariance, alpha))
    projected = tuple(
        sum(coefficient * value for coefficient, value in zip(row, query_covariance))
        for row in inverse
    )
    standardized_variance = max(
        0.0,
        1.0 - sum(a * b for a, b in zip(query_covariance, projected)),
    )
    return (
        mean_value + scale_value * standardized_mean,
        scale_value * math.sqrt(standardized_variance),
    )


def expected_improvement(
    predicted_mean: float,
    predicted_standard_deviation: float,
    incumbent: float,
) -> float:
    """Return the maximization expected-improvement acquisition value."""

    if any(
        not math.isfinite(value)
        for value in (predicted_mean, predicted_standard_deviation, incumbent)
    ):
        raise ValueError("expected-improvement arguments must be finite")
    if predicted_standard_deviation < 0.0:
        raise ValueError("predicted standard deviation cannot be negative")
    improvement = predicted_mean - incumbent
    if predicted_standard_deviation == 0.0:
        return max(0.0, improvement)
    z_score = improvement / predicted_standard_deviation
    normal_cdf = 0.5 * (1.0 + math.erf(z_score / math.sqrt(2.0)))
    normal_pdf = math.exp(-0.5 * z_score**2) / math.sqrt(2.0 * math.pi)
    return improvement * normal_cdf + predicted_standard_deviation * normal_pdf


def _quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("cannot calculate a quantile of empty values")
    position = probability * (len(ordered) - 1)
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def run_bayesian_optimization(
    application: ApplicationSpecification,
    initial_designs: Sequence[PrototypeDesign],
    candidate_designs: Sequence[PrototypeDesign],
    *,
    iterations: int = 12,
    random_repetitions: int = 25,
    seed: int = 20260821,
    current_grid_size: int = 28,
    assembly: ModuleAssemblyAssumptions = ModuleAssemblyAssumptions(),
) -> BayesianOptimizationResult:
    """Compare cost-aware expected improvement with random candidate order."""

    initial = tuple(initial_designs)
    candidates = tuple(candidate_designs)
    if not initial or not candidates:
        raise ValueError("initial and candidate design sets must be nonempty")
    if isinstance(iterations, bool) or not isinstance(iterations, int):
        raise ValueError("iterations must be a positive integer")
    if iterations <= 0 or iterations > len(candidates):
        raise ValueError("iterations must fit inside the candidate set")
    if (
        isinstance(random_repetitions, bool)
        or not isinstance(random_repetitions, int)
        or random_repetitions <= 0
    ):
        raise ValueError("random repetitions must be a positive integer")
    all_ids = tuple(design.design_id for design in initial + candidates)
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("design IDs must be unique")
    evaluation_cache = {
        design.design_id: optimize_design_current(
            design,
            application,
            grid_size=current_grid_size,
            assembly=assembly,
        )
        for design in initial + candidates
    }
    observed = [evaluation_cache[design.design_id] for design in initial]
    available = list(candidates)
    acquired = []
    history = [max(point.utility for point in observed)]
    for _ in range(iterations):
        features = tuple(design_features(point.design) for point in observed)
        values = tuple(point.utility for point in observed)
        incumbent = max(values)
        scored = []
        for design in available:
            predicted_mean, predicted_std = gaussian_process_predict(
                features,
                values,
                design_features(design),
            )
            improvement = expected_improvement(
                predicted_mean,
                predicted_std,
                incumbent,
            )
            acquisition = improvement / math.sqrt(prototype_cost_index(design))
            scored.append((acquisition, predicted_mean, predicted_std, design))
        _, _, _, selected_design = max(
            scored,
            key=lambda item: (item[0], item[1] + 0.1 * item[2]),
        )
        selected = evaluation_cache[selected_design.design_id]
        acquired.append(selected)
        observed.append(selected)
        available.remove(selected_design)
        history.append(max(history[-1], selected.utility))

    random_histories = []
    for repetition in range(random_repetitions):
        generator = random.Random(seed + 1009 * (repetition + 1))
        order = list(candidates)
        generator.shuffle(order)
        best = max(point.utility for point in observed[: len(initial)])
        random_history = [best]
        for design in order[:iterations]:
            best = max(best, evaluation_cache[design.design_id].utility)
            random_history.append(best)
        random_histories.append(tuple(random_history))
    random_median = tuple(
        _quantile(tuple(row[index] for row in random_histories), 0.50)
        for index in range(iterations + 1)
    )
    random_lower = tuple(
        _quantile(tuple(row[index] for row in random_histories), 0.10)
        for index in range(iterations + 1)
    )
    random_upper = tuple(
        _quantile(tuple(row[index] for row in random_histories), 0.90)
        for index in range(iterations + 1)
    )
    oracle = max(evaluation_cache.values(), key=lambda point: point.utility)
    selected = max(observed, key=lambda point: point.utility)
    return BayesianOptimizationResult(
        application,
        tuple(observed[: len(initial)]),
        tuple(acquired),
        tuple(history),
        random_median,
        random_lower,
        random_upper,
        selected,
        oracle,
    )


def _lognormal_unit_mean(generator: random.Random, sigma: float) -> float:
    return math.exp(generator.gauss(-0.5 * sigma**2, sigma))


def run_robustness_study(
    nominal: DesignOperatingPoint,
    *,
    trials: int = 300,
    seed: int = 20260821,
    assembly: ModuleAssemblyAssumptions = ModuleAssemblyAssumptions(),
) -> RobustnessResult:
    """Hold current fixed while perturbing material and interface properties."""

    if isinstance(trials, bool) or trials <= 0:
        raise ValueError("robustness trials must be a positive integer")
    generator = random.Random(seed)
    points = []
    for _ in range(trials):
        multipliers = PropertyMultipliers(
            max(0.80, generator.gauss(1.0, 0.03)),
            max(0.80, generator.gauss(1.0, 0.03)),
            _lognormal_unit_mean(generator, 0.08),
            _lognormal_unit_mean(generator, 0.08),
            _lognormal_unit_mean(generator, 0.08),
            _lognormal_unit_mean(generator, 0.08),
        )
        efficiency = min(0.99, max(0.85, generator.gauss(0.95, 0.01)))
        points.append(
            evaluate_design_current(
                nominal.design,
                nominal.application,
                nominal.mean_current,
                assembly=assembly,
                multipliers=multipliers,
                electrical_contact_resistivity_multiplier=(
                    _lognormal_unit_mean(generator, 0.20)
                ),
                contact_multiplier=_lognormal_unit_mean(generator, 0.15),
                cold_exchanger_multiplier=_lognormal_unit_mean(generator, 0.10),
                hot_exchanger_multiplier=_lognormal_unit_mean(generator, 0.10),
                converter_efficiency=efficiency,
            )
        )
    cooling = tuple(point.delivered_cooling_rate for point in points)
    cop = tuple(point.wall_cooling_cop or 0.0 for point in points)
    hot_face = tuple(point.hot_face_temperature for point in points)
    return RobustnessResult(
        nominal.application,
        nominal,
        trials,
        sum(point.feasible for point in points) / trials,
        (_quantile(cooling, 0.05), _quantile(cooling, 0.50), _quantile(cooling, 0.95)),
        (_quantile(cop, 0.05), _quantile(cop, 0.50), _quantile(cop, 0.95)),
        (
            _quantile(hot_face, 0.05),
            _quantile(hot_face, 0.50),
            _quantile(hot_face, 0.95),
        ),
    )


def run_codesign_campaign(
    config: CodesignCampaignConfig = CodesignCampaignConfig(),
) -> CodesignCampaignResult:
    """Run all three reproducible co-design experiments."""

    initial_designs = generate_space_filling_designs(
        config.initial_design_count,
        seed=config.seed,
        prefix="initial",
    )
    candidate_designs = generate_space_filling_designs(
        config.candidate_design_count,
        seed=config.seed + 1,
        prefix="candidate",
    )
    initial_summaries = []
    bayesian_results = []
    robustness_results = []
    for application_index, application in enumerate(APPLICATION_SPECIFICATIONS):
        initial_evaluations = tuple(
            optimize_design_current(
                design,
                application,
                grid_size=config.current_grid_size,
                assembly=config.assembly,
            )
            for design in initial_designs
        )
        initial_summaries.append(
            InitialDesignSummary(
                application,
                initial_evaluations,
                sum(point.feasible for point in initial_evaluations),
                max(initial_evaluations, key=lambda point: point.utility),
            )
        )
        bayesian = run_bayesian_optimization(
            application,
            initial_designs,
            candidate_designs,
            iterations=config.bayesian_iterations,
            random_repetitions=config.random_search_repetitions,
            seed=config.seed + 100 * application_index,
            current_grid_size=config.current_grid_size,
            assembly=config.assembly,
        )
        bayesian_results.append(bayesian)
        robustness_results.append(
            run_robustness_study(
                bayesian.selected,
                trials=config.robustness_trials,
                seed=config.seed + 10000 * (application_index + 1),
                assembly=config.assembly,
            )
        )
    return CodesignCampaignResult(
        config,
        initial_designs,
        candidate_designs,
        tuple(initial_summaries),
        tuple(bayesian_results),
        tuple(robustness_results),
    )


def format_codesign_campaign_report(result: CodesignCampaignResult) -> str:
    """Return a compact, reproducible plain-text result summary."""

    assembly = result.config.assembly
    lines = [
        "ThermoTwin material/geometry Bayesian co-design campaign",
        (
            "specific electrical contact resistivity: "
            f"{assembly.specific_electrical_contact_resistivity:.2e} ohm m^2 "
            "per metal/TE interface"
        ),
        (
            f"budget: {result.config.initial_design_count} initial + "
            f"{result.config.bayesian_iterations} selected prototypes per application"
        ),
        (
            f"candidate pool: {result.config.candidate_design_count}; "
            f"random baselines: {result.config.random_search_repetitions}; "
            f"robustness trials: {result.config.robustness_trials}"
        ),
    ]
    for summary, bayesian, robustness in zip(
        result.initial_summaries,
        result.bayesian_results,
        result.robustness_results,
    ):
        selected = bayesian.selected
        lines.extend(
            (
                "",
                f"{summary.application.label}:",
                (
                    f"  initial feasible: {summary.feasible_count}/"
                    f"{len(summary.evaluations)}"
                ),
                (
                    f"  selected: {selected.design.design_id}, "
                    f"p={selected.design.p_material.sample_id}, "
                    f"n={selected.design.n_material.sample_id}, "
                    f"N={selected.design.geometry.couple_count}, "
                    f"L={selected.design.geometry.leg_length * 1e3:.3f} mm, "
                    f"A={selected.design.geometry.leg_area * 1e6:.3f} mm^2"
                ),
                (
                    f"  operating point: I={selected.mean_current:.3f} A, "
                    f"Qc={selected.delivered_cooling_rate:.3f} W, "
                    f"wall COP={selected.wall_cooling_cop:.3f}, "
                    f"cost index={selected.prototype_cost_index:.3f}"
                ),
                (
                    "  electrical resistance: "
                    f"bulk={selected.bulk_leg_electrical_resistance:.4f} ohm, "
                    f"contacts={selected.electrical_contact_resistance:.4f} ohm "
                    f"({100.0 * selected.electrical_contact_resistance / selected.thermoelectric_parameters.electrical_resistance:.1f}% total)"
                ),
                (
                    "  peak current density: "
                    f"{selected.peak_current_density / 1.0e6:.4f} A/mm^2, "
                    f"{100.0 * selected.current_density_utilization:.2f}% of limit, "
                    "binding="
                    f"{'yes' if selected.current_density_constraint_binding else 'no'}"
                ),
                (
                    f"  utility: initial={bayesian.best_utility_history[0]:.4f}, "
                    f"Bayesian={bayesian.best_utility_history[-1]:.4f}, "
                    f"random median={bayesian.random_median_history[-1]:.4f}, "
                    f"pool oracle={bayesian.oracle_best.utility:.4f}"
                ),
                (
                    f"  fixed-current robustness: {100 * robustness.feasible_fraction:.1f}% "
                    f"feasible; Qc 5/50/95%="
                    f"{robustness.cooling_rate_quantiles[0]:.3f}/"
                    f"{robustness.cooling_rate_quantiles[1]:.3f}/"
                    f"{robustness.cooling_rate_quantiles[2]:.3f} W; "
                    f"COP 5/50/95%="
                    f"{robustness.wall_cop_quantiles[0]:.3f}/"
                    f"{robustness.wall_cop_quantiles[1]:.3f}/"
                    f"{robustness.wall_cop_quantiles[2]:.3f}"
                ),
            )
        )
    return "\n".join(lines)


def main() -> None:
    """Run the default CPU-first campaign and print its text report."""

    print(format_codesign_campaign_report(run_codesign_campaign()))


if __name__ == "__main__":
    main()
