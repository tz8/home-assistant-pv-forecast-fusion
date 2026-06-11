"""Coordinator for PV Forecast Fusion."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN, SOURCE_SLOTS
from .fusion import ForecastSource, HourlyForecastPoint, fuse_sources
from .source_entity_groups import aggregate_curve_values, aggregate_numeric_values, expand_entity_group
from .source_parser import extract_curve_values, extract_hourly_energy_forecast
from .source_presets import derive_remaining_from_attributes


_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class SourceSnapshot:
    name: str
    configured_source_type: str
    source_type: str
    resolution_basis: str
    today_entity: str | None
    tomorrow_entity: str | None
    remaining_entity: str | None
    today_entities: list[str]
    tomorrow_entities: list[str]
    remaining_entities: list[str]
    remaining_method: str | None
    remaining_methods: list[str]
    today_kwh: float | None
    tomorrow_kwh: float | None
    remaining_today_kwh: float | None
    weight: float
    bias_factor: float
    confidence: float
    curve_points: int


class PvForecastFusionCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate fused forecast state."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES),
        )
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        sources: list[ForecastSource] = []
        snapshots: list[SourceSnapshot] = []

        for slot in SOURCE_SLOTS:
            source, snapshot = _build_source_from_entry(self.hass, self.entry, slot)
            if source is None or snapshot is None:
                continue
            sources.append(source)
            snapshots.append(snapshot)

        result = fuse_sources(sources)
        return {
            "name": self.entry.data.get(CONF_NAME),
            "result": result,
            "sources": [asdict(snapshot) for snapshot in snapshots],
        }


def _build_source_from_entry(
    hass: HomeAssistant, entry: ConfigEntry, slot: int
) -> tuple[ForecastSource | None, SourceSnapshot | None]:
    name = _entry_value(entry, f"source_{slot}_name") or f"source_{slot}"
    configured_source_type = _entry_value(entry, f"source_{slot}_type") or "auto"
    today_entities_value = _entry_value(entry, f"source_{slot}_today_entity")
    explicit_tomorrow_entities_value = _entry_value(entry, f"source_{slot}_tomorrow_entity")
    explicit_remaining_entities_value = _entry_value(entry, f"source_{slot}_remaining_entity")
    weight = _float_or_default(_entry_value(entry, f"source_{slot}_weight"), 1.0)
    bias_factor = _float_or_default(_entry_value(entry, f"source_{slot}_bias_factor"), 1.0)
    confidence = _float_or_default(_entry_value(entry, f"source_{slot}_confidence"), 1.0)

    if not today_entities_value:
        return None, None

    raw_today_entities = [item.strip() for item in str(today_entities_value).split(",") if item.strip()]
    attributes_by_today_entity: dict[str, dict[str, Any] | None] = {}
    for entity_id in raw_today_entities:
        state = hass.states.get(entity_id)
        attributes_by_today_entity[entity_id] = state.attributes if state else None

    resolved_group = expand_entity_group(
        today_entities=today_entities_value,
        tomorrow_entities=explicit_tomorrow_entities_value,
        remaining_entities=explicit_remaining_entities_value,
        attributes_by_today_entity=attributes_by_today_entity,
        configured_source_type=configured_source_type,
    )
    if not resolved_group.items:
        return None, None

    resolved_today_entities = [item.today_entity for item in resolved_group.items if item.today_entity]
    resolved_tomorrow_entities = [item.tomorrow_entity for item in resolved_group.items if item.tomorrow_entity]
    resolved_remaining_entities = [item.remaining_entity for item in resolved_group.items if item.remaining_entity]

    source_types: list[str] = []
    resolution_bases: list[str] = []
    today_values: list[float | None] = []
    tomorrow_values: list[float | None] = []
    remaining_values: list[float | None] = []
    remaining_methods: list[str] = []
    curves: list[list[float]] = []
    today_hourly_points: list[list[HourlyForecastPoint]] = []
    tomorrow_hourly_points: list[list[HourlyForecastPoint]] = []

    now = datetime.now(timezone.utc)
    for resolved in resolved_group.items:
        source_types.append(resolved.source_type)
        resolution_bases.append(resolved.resolution_basis)

        today_state = hass.states.get(resolved.today_entity)
        tomorrow_state = hass.states.get(resolved.tomorrow_entity) if resolved.tomorrow_entity else None
        remaining_state = hass.states.get(resolved.remaining_entity) if resolved.remaining_entity else None

        today_values.append(_state_to_float(today_state.state if today_state else None))
        tomorrow_values.append(_state_to_float(tomorrow_state.state if tomorrow_state else None))

        remaining_today_kwh = _state_to_float(remaining_state.state if remaining_state else None)
        remaining_method = "direct_sensor" if remaining_today_kwh is not None and resolved.remaining_entity else None
        if remaining_today_kwh is None and today_state is not None:
            remaining_today_kwh = derive_remaining_from_attributes(
                source_type=resolved.source_type,
                attributes=today_state.attributes,
                now=now,
            )
            if remaining_today_kwh is not None:
                remaining_method = "derived_from_today_attributes"

        remaining_values.append(remaining_today_kwh)
        remaining_methods.append(remaining_method or "unavailable")
        curves.append(extract_curve_values(today_state.attributes if today_state else None))
        today_hourly_points.append(extract_hourly_energy_forecast(today_state.attributes if today_state else None))
        tomorrow_hourly_points.append(
            extract_hourly_energy_forecast(tomorrow_state.attributes if tomorrow_state else None)
        )

    today_kwh = aggregate_numeric_values(today_values)
    tomorrow_kwh = aggregate_numeric_values(tomorrow_values)
    remaining_today_kwh = aggregate_numeric_values(remaining_values)
    curve_values = aggregate_curve_values(curves)
    today_hourly = _aggregate_hourly_points(today_hourly_points)
    tomorrow_hourly = _aggregate_hourly_points(tomorrow_hourly_points)

    source = ForecastSource(
        name=name,
        today_kwh=today_kwh,
        tomorrow_kwh=tomorrow_kwh,
        remaining_today_kwh=remaining_today_kwh,
        weight=weight,
        bias_factor=bias_factor,
        confidence=confidence,
        curve_values=curve_values,
        hourly_today=today_hourly,
        hourly_tomorrow=tomorrow_hourly,
    )
    snapshot = SourceSnapshot(
        name=name,
        configured_source_type=resolved_group.items[0].configured_source_type,
        source_type=_single_value_or_mixed(source_types),
        resolution_basis=_single_value_or_mixed(resolution_bases),
        today_entity=_single_entity_or_none(resolved_today_entities),
        tomorrow_entity=_single_entity_or_none(resolved_tomorrow_entities),
        remaining_entity=_single_entity_or_none(resolved_remaining_entities),
        today_entities=resolved_today_entities,
        tomorrow_entities=resolved_tomorrow_entities,
        remaining_entities=resolved_remaining_entities,
        remaining_method=_single_optional_value_or_mixed(
            [method for method in remaining_methods if method != "unavailable"]
        ),
        remaining_methods=remaining_methods,
        today_kwh=source.today_kwh,
        tomorrow_kwh=source.tomorrow_kwh,
        remaining_today_kwh=source.remaining_today_kwh,
        weight=weight,
        bias_factor=bias_factor,
        confidence=confidence,
        curve_points=len(curve_values),
    )
    return source, snapshot


def _entry_value(entry: ConfigEntry, key: str) -> Any:
    value = entry.data.get(key)
    if isinstance(value, str):
        value = value.strip()
    return value


def _state_to_float(value: str | None) -> float | None:
    if value in (None, "", "unknown", "unavailable"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _single_entity_or_none(values: list[str]) -> str | None:
    if len(values) == 1:
        return values[0]
    return None


def _single_value_or_mixed(values: list[str], mixed_value: str = "mixed") -> str:
    unique_values = list(dict.fromkeys(values))
    if len(unique_values) == 1:
        return unique_values[0]
    return mixed_value


def _single_optional_value_or_mixed(values: list[str], mixed_value: str = "mixed") -> str | None:
    if not values:
        return None
    unique_values = list(dict.fromkeys(values))
    if len(unique_values) == 1:
        return unique_values[0]
    return mixed_value


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _aggregate_hourly_points(grouped_points: list[list[HourlyForecastPoint]]) -> list[HourlyForecastPoint]:
    buckets: dict[datetime, float] = {}
    for points in grouped_points:
        for point in points:
            buckets[point.period_start] = buckets.get(point.period_start, 0.0) + point.energy_kwh
    return [
        HourlyForecastPoint(period_start=period_start, energy_kwh=energy_kwh)
        for period_start, energy_kwh in sorted(buckets.items())
    ]
