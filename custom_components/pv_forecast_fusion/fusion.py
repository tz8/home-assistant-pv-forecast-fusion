"""Pure fusion logic for PV forecast fusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(slots=True)
class ForecastSource:
    name: str
    today_kwh: float | None = None
    tomorrow_kwh: float | None = None
    remaining_today_kwh: float | None = None
    weight: float = 1.0
    bias_factor: float = 1.0
    confidence: float = 1.0
    curve_values: list[float] | None = None

    @property
    def effective_weight(self) -> float:
        return max(0.0, float(self.weight) * float(self.confidence))


@dataclass(slots=True)
class FusionMetricDetails:
    value: float | None
    contributing_sources: list[str]
    effective_weights: dict[str, float]


@dataclass(slots=True)
class FusionResult:
    today_kwh: float | None
    tomorrow_kwh: float | None
    remaining_today_kwh: float | None
    weather_pattern: str
    active_source_names: list[str]
    metric_details: dict[str, FusionMetricDetails]


def fuse_sources(sources: Iterable[ForecastSource]) -> FusionResult:
    source_list = list(sources)
    today = _fuse_metric(source_list, "today_kwh")
    tomorrow = _fuse_metric(source_list, "tomorrow_kwh")
    remaining = _fuse_metric(source_list, "remaining_today_kwh")

    active_names = sorted(
        {
            *today.contributing_sources,
            *tomorrow.contributing_sources,
            *remaining.contributing_sources,
        },
        key=lambda name: [s.name for s in source_list].index(name),
    )

    weather_curve = _best_curve(source_list)
    weather_pattern = classify_weather_pattern(weather_curve)

    return FusionResult(
        today_kwh=today.value,
        tomorrow_kwh=tomorrow.value,
        remaining_today_kwh=remaining.value,
        weather_pattern=weather_pattern,
        active_source_names=active_names,
        metric_details={
            "today_kwh": today,
            "tomorrow_kwh": tomorrow,
            "remaining_today_kwh": remaining,
        },
    )


def _fuse_metric(sources: Sequence[ForecastSource], field_name: str) -> FusionMetricDetails:
    numerator = 0.0
    denominator = 0.0
    contributing: list[str] = []
    weights: dict[str, float] = {}

    for source in sources:
        value = getattr(source, field_name)
        effective_weight = source.effective_weight
        if value is None or effective_weight <= 0:
            continue
        numerator += float(value) * float(source.bias_factor) * effective_weight
        denominator += effective_weight
        contributing.append(source.name)
        weights[source.name] = effective_weight

    if denominator <= 0:
        return FusionMetricDetails(value=None, contributing_sources=[], effective_weights={})

    return FusionMetricDetails(
        value=numerator / denominator,
        contributing_sources=contributing,
        effective_weights=weights,
    )


def _best_curve(sources: Sequence[ForecastSource]) -> list[float]:
    curves = [source.curve_values for source in sources if source.curve_values]
    if not curves:
        return []
    curves.sort(key=len, reverse=True)
    return [float(v) for v in curves[0] if isinstance(v, (int, float))]


def classify_weather_pattern(curve_values: Sequence[float]) -> str:
    values = [max(0.0, float(v)) for v in curve_values if isinstance(v, (int, float))]
    if len(values) < 5 or max(values, default=0.0) <= 0:
        return "unknown"

    peak = max(values)
    mean = sum(values) / len(values)
    sign_changes = _sign_changes(values)
    peak_to_mean = peak / mean if mean else 0.0

    if sign_changes >= 4:
        return "variable"
    if peak < 250:
        return "overcast"
    if sign_changes <= 1 and peak_to_mean >= 1.45:
        return "sunny"
    return "mixed"


def _sign_changes(values: Sequence[float]) -> int:
    deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    signs: list[int] = []
    for delta in deltas:
        if abs(delta) < 1e-9:
            continue
        signs.append(1 if delta > 0 else -1)

    changes = 0
    for previous, current in zip(signs, signs[1:]):
        if previous != current:
            changes += 1
    return changes
