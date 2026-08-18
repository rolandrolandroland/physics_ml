"""Conventional inference of one cold thermal contact resistance."""

from dataclasses import dataclass, replace
import math
from typing import NamedTuple, Sequence, Tuple

from .contact_experiments import (
    FourNodeContactExperiment,
    constant_current_contact_reference_experiment,
    run_four_node_contact_experiment,
)
from .controls import PiecewiseConstantCurrent
from .virtual_test_stand import (
    ObservationDataset,
    ideal_four_sensor_test_stand,
    observe_contact_trajectory,
)


REFERENCE_COLD_CONTACT_RESISTANCE = 0.25
FITTED_SENSOR_NAMES = (
    "cold_face_sensor",
    "cold_exchanger_sensor",
)
ALL_SENSOR_NAMES = (
    "cold_face_sensor",
    "hot_face_sensor",
    "cold_exchanger_sensor",
    "hot_exchanger_sensor",
)


@dataclass(frozen=True)
class ContactResistanceRegime:
    """One named current schedule assigned to one whole-data split."""

    name: str
    split: str
    current: PiecewiseConstantCurrent

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("regime name must be nonempty")
        object.__setattr__(self, "name", self.name.strip())
        if (
            not isinstance(self.split, str)
            or self.split not in {"train", "validation", "test"}
        ):
            raise ValueError(
                "regime split must be 'train', 'validation', or 'test'"
            )
        if not isinstance(self.current, PiecewiseConstantCurrent):
            raise ValueError("regime current must be piecewise constant")


@dataclass(frozen=True)
class ContactResistanceRegimeDataset:
    """One complete regime and its ideal long-form observations."""

    regime: ContactResistanceRegime
    observations: ObservationDataset

    def __post_init__(self) -> None:
        if not isinstance(self.regime, ContactResistanceRegime):
            raise ValueError("regime dataset must contain a valid regime")
        if not isinstance(self.observations, ObservationDataset):
            raise ValueError(
                "regime dataset must contain an observation dataset"
            )


@dataclass(frozen=True)
class ContactResistanceDatasetSplit:
    """Whole experiments assigned without random time-point leakage."""

    train: Tuple[ContactResistanceRegimeDataset, ...]
    validation: Tuple[ContactResistanceRegimeDataset, ...]
    test: Tuple[ContactResistanceRegimeDataset, ...]

    def __post_init__(self) -> None:
        try:
            groups = {
                "train": tuple(self.train),
                "validation": tuple(self.validation),
                "test": tuple(self.test),
            }
        except TypeError as error:
            raise ValueError(
                "dataset splits must be collections of regime datasets"
            ) from error
        for name, datasets in groups.items():
            if not datasets:
                raise ValueError(f"{name} dataset split must be nonempty")
            if not all(
                isinstance(dataset, ContactResistanceRegimeDataset)
                for dataset in datasets
            ):
                raise ValueError(
                    "dataset splits must contain regime datasets"
                )
            if any(dataset.regime.split != name for dataset in datasets):
                raise ValueError(
                    f"every {name} dataset must have the matching split"
                )
            object.__setattr__(self, name, datasets)

        names = tuple(
            dataset.regime.name
            for datasets in groups.values()
            for dataset in datasets
        )
        if len(set(names)) != len(names):
            raise ValueError("regime names must be unique across all splits")


@dataclass(frozen=True)
class ContactResistanceSearchConfig:
    """Bounds and stopping settings for scalar golden-section search."""

    lower_bound: float = 0.05
    upper_bound: float = 1.0
    resistance_tolerance: float = 1e-8
    max_iterations: int = 96

    def __post_init__(self) -> None:
        for name, value in (
            ("lower bound", self.lower_bound),
            ("upper bound", self.upper_bound),
            ("resistance tolerance", self.resistance_tolerance),
        ):
            try:
                value_is_finite = math.isfinite(value)
            except TypeError as error:
                raise ValueError(
                    f"{name} must be finite and positive"
                ) from error
            if not value_is_finite or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.upper_bound <= self.lower_bound:
            raise ValueError("upper bound must exceed lower bound")
        if (
            not isinstance(self.max_iterations, int)
            or isinstance(self.max_iterations, bool)
            or self.max_iterations <= 0
        ):
            raise ValueError("maximum iterations must be a positive integer")


class ContactResistanceLossEvaluation(NamedTuple):
    """One candidate resistance and its training temperature MSE."""

    cold_contact_resistance: float
    mean_squared_error: float


class ContactResistanceFitResult(NamedTuple):
    """Best scalar estimate and its complete search history."""

    inferred_cold_contact_resistance: float
    training_mean_squared_error: float
    iterations: int
    evaluations: Tuple[ContactResistanceLossEvaluation, ...]


class ContactResistanceRegimeMetrics(NamedTuple):
    """Temperature RMSE values for one held-together experiment."""

    regime_name: str
    split: str
    cold_face_rmse: float
    cold_exchanger_rmse: float
    hot_face_rmse: float
    hot_exchanger_rmse: float
    fitted_pair_rmse: float
    all_sensor_rmse: float


class ContactResistanceInferenceSummary(NamedTuple):
    """Parameter, sensitivity, and regime-level validation results."""

    true_cold_contact_resistance: float
    inferred_cold_contact_resistance: float
    absolute_parameter_error: float
    relative_parameter_error_percent: float
    sensitivity: Tuple[ContactResistanceLossEvaluation, ...]
    training_metrics: Tuple[ContactResistanceRegimeMetrics, ...]
    validation_metrics: Tuple[ContactResistanceRegimeMetrics, ...]
    test_metrics: Tuple[ContactResistanceRegimeMetrics, ...]


class ContactResistanceInferenceExperimentResult(NamedTuple):
    """Frozen datasets, scalar fit, and post-fit synthetic validation."""

    datasets: ContactResistanceDatasetSplit
    fit: ContactResistanceFitResult
    summary: ContactResistanceInferenceSummary


def reference_contact_resistance_regimes(
) -> Tuple[ContactResistanceRegime, ...]:
    """Return the frozen train, validation, and test current regimes."""

    return (
        ContactResistanceRegime(
            name="unipolar_training_pulse",
            split="train",
            current=PiecewiseConstantCurrent.pulse(
                start_time=5.0,
                end_time=20.0,
                pulse_current=1.0,
            ),
        ),
        ContactResistanceRegime(
            name="lower_amplitude_validation_pulse",
            split="validation",
            current=PiecewiseConstantCurrent.pulse(
                start_time=10.0,
                end_time=30.0,
                pulse_current=0.6,
            ),
        ),
        ContactResistanceRegime(
            name="bipolar_test_pulse",
            split="test",
            current=PiecewiseConstantCurrent(
                transition_times=(5.0, 20.0, 35.0, 50.0),
                values=(0.0, 1.0, 0.0, -1.0, 0.0),
            ),
        ),
    )


def contact_resistance_experiment(
    regime: ContactResistanceRegime,
    *,
    cold_contact_resistance: float,
) -> FourNodeContactExperiment:
    """Build one regime with one explicit positive candidate resistance."""

    try:
        resistance_is_finite = math.isfinite(cold_contact_resistance)
    except TypeError as error:
        raise ValueError(
            "cold contact resistance must be finite and positive"
        ) from error
    if not resistance_is_finite or cold_contact_resistance <= 0.0:
        raise ValueError(
            "cold contact resistance must be finite and positive"
        )
    reference = constant_current_contact_reference_experiment()
    thermal_parameters = replace(
        reference.thermal_parameters,
        cold_contact_resistance=float(cold_contact_resistance),
    )
    return replace(
        reference,
        thermal_parameters=thermal_parameters,
        current=regime.current,
    )


def simulate_contact_resistance_observations(
    regime: ContactResistanceRegime,
    *,
    cold_contact_resistance: float,
    sampling_interval: float = 1.0,
) -> ObservationDataset:
    """Simulate ideal observations without returning dense hidden truth."""

    experiment = contact_resistance_experiment(
        regime,
        cold_contact_resistance=cold_contact_resistance,
    )
    trajectory = run_four_node_contact_experiment(experiment).trajectory
    return observe_contact_trajectory(
        trajectory,
        current=regime.current,
        test_stand=ideal_four_sensor_test_stand(
            sampling_interval=sampling_interval
        ),
    )


def reference_contact_resistance_dataset_split(
    *,
    sampling_interval: float = 1.0,
) -> ContactResistanceDatasetSplit:
    """Generate ideal observations and split complete regimes by name."""

    groups = {"train": [], "validation": [], "test": []}
    for regime in reference_contact_resistance_regimes():
        groups[regime.split].append(
            ContactResistanceRegimeDataset(
                regime=regime,
                observations=simulate_contact_resistance_observations(
                    regime,
                    cold_contact_resistance=(
                        REFERENCE_COLD_CONTACT_RESISTANCE
                    ),
                    sampling_interval=sampling_interval,
                ),
            )
        )
    return ContactResistanceDatasetSplit(
        train=tuple(groups["train"]),
        validation=tuple(groups["validation"]),
        test=tuple(groups["test"]),
    )


def _paired_temperature_errors(
    predicted: ObservationDataset,
    observed: ObservationDataset,
    sensor_names: Sequence[str],
) -> Tuple[float, ...]:
    errors = []
    for sensor_name in sensor_names:
        predicted_history = predicted.observations_for(sensor_name)
        observed_history = observed.observations_for(sensor_name)
        if tuple(item.time for item in predicted_history) != tuple(
            item.time for item in observed_history
        ):
            raise ValueError("predicted and observed times must match")
        errors.extend(
            prediction.temperature - measurement.temperature
            for prediction, measurement in zip(
                predicted_history,
                observed_history,
            )
        )
    if not errors:
        raise ValueError("at least one paired temperature is required")
    return tuple(errors)


def _mean_squared_error(errors: Sequence[float]) -> float:
    if not errors:
        raise ValueError("at least one error is required")
    return sum(error * error for error in errors) / len(errors)


def _root_mean_squared_error(errors: Sequence[float]) -> float:
    return math.sqrt(_mean_squared_error(errors))


def contact_resistance_training_loss(
    cold_contact_resistance: float,
    training_datasets: Sequence[ContactResistanceRegimeDataset],
) -> float:
    """Return equal-weight cold-face/exchanger temperature MSE in K^2."""

    if not training_datasets:
        raise ValueError("at least one training regime is required")
    all_errors = []
    for dataset in training_datasets:
        predicted = simulate_contact_resistance_observations(
            dataset.regime,
            cold_contact_resistance=cold_contact_resistance,
            sampling_interval=dataset.observations.sampling_interval,
        )
        all_errors.extend(
            _paired_temperature_errors(
                predicted,
                dataset.observations,
                FITTED_SENSOR_NAMES,
            )
        )
    return _mean_squared_error(tuple(all_errors))


def fit_cold_contact_resistance(
    training_datasets: Sequence[ContactResistanceRegimeDataset],
    config: ContactResistanceSearchConfig = ContactResistanceSearchConfig(),
) -> ContactResistanceFitResult:
    """Fit one positive resistance with dependency-free golden search."""

    training_datasets = tuple(training_datasets)
    if not training_datasets:
        raise ValueError("at least one training regime is required")
    if any(
        dataset.regime.split != "train"
        for dataset in training_datasets
    ):
        raise ValueError("only training regimes may enter the fit")

    evaluations = []

    def evaluate(candidate: float) -> float:
        loss = contact_resistance_training_loss(
            candidate,
            training_datasets,
        )
        evaluations.append(
            ContactResistanceLossEvaluation(candidate, loss)
        )
        return loss

    left = config.lower_bound
    right = config.upper_bound
    golden_ratio = 0.5 * (1.0 + math.sqrt(5.0))
    interior_left = right - (right - left) / golden_ratio
    interior_right = left + (right - left) / golden_ratio
    left_loss = evaluate(interior_left)
    right_loss = evaluate(interior_right)

    iterations = 0
    while (
        right - left > config.resistance_tolerance
        and iterations < config.max_iterations
    ):
        if left_loss <= right_loss:
            right = interior_right
            interior_right = interior_left
            right_loss = left_loss
            interior_left = right - (right - left) / golden_ratio
            left_loss = evaluate(interior_left)
        else:
            left = interior_left
            interior_left = interior_right
            left_loss = right_loss
            interior_right = left + (right - left) / golden_ratio
            right_loss = evaluate(interior_right)
        iterations += 1

    inferred_resistance = 0.5 * (left + right)
    inferred_loss = evaluate(inferred_resistance)
    return ContactResistanceFitResult(
        inferred_cold_contact_resistance=inferred_resistance,
        training_mean_squared_error=inferred_loss,
        iterations=iterations,
        evaluations=tuple(evaluations),
    )


def evaluate_contact_resistance_regime(
    cold_contact_resistance: float,
    dataset: ContactResistanceRegimeDataset,
) -> ContactResistanceRegimeMetrics:
    """Evaluate fitted and withheld sensor errors for one whole regime."""

    predicted = simulate_contact_resistance_observations(
        dataset.regime,
        cold_contact_resistance=cold_contact_resistance,
        sampling_interval=dataset.observations.sampling_interval,
    )
    sensor_errors = {
        sensor_name: _paired_temperature_errors(
            predicted,
            dataset.observations,
            (sensor_name,),
        )
        for sensor_name in ALL_SENSOR_NAMES
    }
    fitted_errors = tuple(
        error
        for sensor_name in FITTED_SENSOR_NAMES
        for error in sensor_errors[sensor_name]
    )
    all_errors = tuple(
        error
        for sensor_name in ALL_SENSOR_NAMES
        for error in sensor_errors[sensor_name]
    )
    return ContactResistanceRegimeMetrics(
        regime_name=dataset.regime.name,
        split=dataset.regime.split,
        cold_face_rmse=_root_mean_squared_error(
            sensor_errors["cold_face_sensor"]
        ),
        cold_exchanger_rmse=_root_mean_squared_error(
            sensor_errors["cold_exchanger_sensor"]
        ),
        hot_face_rmse=_root_mean_squared_error(
            sensor_errors["hot_face_sensor"]
        ),
        hot_exchanger_rmse=_root_mean_squared_error(
            sensor_errors["hot_exchanger_sensor"]
        ),
        fitted_pair_rmse=_root_mean_squared_error(fitted_errors),
        all_sensor_rmse=_root_mean_squared_error(all_errors),
    )


def run_contact_resistance_inference_experiment(
    config: ContactResistanceSearchConfig = ContactResistanceSearchConfig(),
) -> ContactResistanceInferenceExperimentResult:
    """Run the frozen ideal fit and evaluate two unseen current regimes."""

    datasets = reference_contact_resistance_dataset_split()
    fit = fit_cold_contact_resistance(datasets.train, config)
    inferred = fit.inferred_cold_contact_resistance
    absolute_error = abs(
        inferred - REFERENCE_COLD_CONTACT_RESISTANCE
    )
    sensitivity = tuple(
        ContactResistanceLossEvaluation(
            candidate,
            contact_resistance_training_loss(candidate, datasets.train),
        )
        for candidate in (0.10, 0.25, 0.50)
    )
    summary = ContactResistanceInferenceSummary(
        true_cold_contact_resistance=(
            REFERENCE_COLD_CONTACT_RESISTANCE
        ),
        inferred_cold_contact_resistance=inferred,
        absolute_parameter_error=absolute_error,
        relative_parameter_error_percent=(
            100.0
            * absolute_error
            / REFERENCE_COLD_CONTACT_RESISTANCE
        ),
        sensitivity=sensitivity,
        training_metrics=tuple(
            evaluate_contact_resistance_regime(inferred, dataset)
            for dataset in datasets.train
        ),
        validation_metrics=tuple(
            evaluate_contact_resistance_regime(inferred, dataset)
            for dataset in datasets.validation
        ),
        test_metrics=tuple(
            evaluate_contact_resistance_regime(inferred, dataset)
            for dataset in datasets.test
        ),
    )
    return ContactResistanceInferenceExperimentResult(
        datasets=datasets,
        fit=fit,
        summary=summary,
    )


def format_contact_resistance_inference_report(
    result: ContactResistanceInferenceExperimentResult,
) -> str:
    """Format a compact reproducible text report."""

    summary = result.summary
    lines = [
        "cold contact resistance inference",
        (
            "true resistance: "
            f"{summary.true_cold_contact_resistance:.9f} K/W"
        ),
        (
            "inferred resistance: "
            f"{summary.inferred_cold_contact_resistance:.9f} K/W"
        ),
        (
            "relative parameter error: "
            f"{summary.relative_parameter_error_percent:.6e} %"
        ),
        f"search evaluations: {len(result.fit.evaluations)}",
    ]
    for metrics in (
        summary.training_metrics
        + summary.validation_metrics
        + summary.test_metrics
    ):
        lines.append(
            f"{metrics.split} {metrics.regime_name}: "
            f"fitted-pair RMSE={metrics.fitted_pair_rmse:.6e} K, "
            f"all-sensor RMSE={metrics.all_sensor_rmse:.6e} K"
        )
    return "\n".join(lines)


def main() -> None:
    """Run and print the frozen CPU-first conventional inference."""

    print(
        format_contact_resistance_inference_report(
            run_contact_resistance_inference_experiment()
        )
    )


if __name__ == "__main__":
    main()
