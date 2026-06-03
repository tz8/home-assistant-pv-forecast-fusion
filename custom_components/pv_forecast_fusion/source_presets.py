"""Preset detection and auto-mapping for known PV forecast providers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .const import DEFAULT_SOURCE_TYPE, SOURCE_TYPE_OPTIONS


@dataclass(slots=True)
class ResolvedSourceEntities:
    configured_source_type: str
    source_type: str
    today_entity: str
    tomorrow_entity: str | None
    remaining_entity: str | None
    auto_mapped: bool
    resolution_basis: str


def normalize_source_entities(
    today_entity: str | None,
    tomorrow_entity: str | None,
    remaining_entity: str | None,
    attributes: dict[str, Any] | None,
    configured_source_type: str | None = None,
) -> ResolvedSourceEntities:
    today_entity = (today_entity or "").strip()
    today_entity = today_entity or None
    tomorrow_entity = _clean_entity_id(tomorrow_entity)
    remaining_entity = _clean_entity_id(remaining_entity)
    configured_source_type = _normalize_source_type(configured_source_type)

    source_type, resolution_basis = _resolve_source_type(today_entity, attributes, configured_source_type)
    auto_mapped = False

    if today_entity is None:
        return ResolvedSourceEntities(
            configured_source_type=configured_source_type,
            source_type=source_type,
            today_entity="",
            tomorrow_entity=tomorrow_entity,
            remaining_entity=remaining_entity,
            auto_mapped=False,
            resolution_basis=resolution_basis,
        )

    inferred_tomorrow, inferred_remaining = infer_related_entities(today_entity, source_type)
    if not tomorrow_entity and inferred_tomorrow:
        tomorrow_entity = inferred_tomorrow
        auto_mapped = True
    if not remaining_entity and inferred_remaining:
        remaining_entity = inferred_remaining
        auto_mapped = True

    return ResolvedSourceEntities(
        configured_source_type=configured_source_type,
        source_type=source_type,
        today_entity=today_entity,
        tomorrow_entity=tomorrow_entity,
        remaining_entity=remaining_entity,
        auto_mapped=auto_mapped,
        resolution_basis=resolution_basis,
    )


def detect_source_type(entity_id: str | None, attributes: dict[str, Any] | None = None) -> str:
    entity_id = (entity_id or "").strip().lower()
    attributes = attributes or {}

    if "solcast_pv_forecast" in entity_id or isinstance(attributes.get("detailedForecast"), list):
        return "solcast"
    if entity_id.startswith("sensor.energy_production_today") or entity_id.startswith("sensor.forecast_solar_"):
        return "forecast_solar"
    if entity_id.endswith("_energy_production_today") or entity_id.endswith("_energy_production_today_2"):
        return "open_meteo"
    return "manual"


def infer_related_entities(today_entity: str, source_type: str) -> tuple[str | None, str | None]:
    if source_type == "solcast" and today_entity.endswith("_prognose_heute"):
        return today_entity.removesuffix("_prognose_heute") + "_prognose_morgen", None

    if source_type == "open_meteo" and "energy_production_today" in today_entity:
        tomorrow_entity = today_entity.replace("energy_production_today", "energy_production_tomorrow")
        remaining_entity = today_entity.replace("energy_production_today", "energy_production_today_remaining")
        return tomorrow_entity, remaining_entity

    if source_type == "forecast_solar" and "energy_production_today" in today_entity:
        tomorrow_entity = today_entity.replace("energy_production_today", "energy_production_tomorrow")
        remaining_entity = today_entity.replace("energy_production_today", "energy_production_today_remaining")
        return tomorrow_entity, remaining_entity

    return None, None


def derive_remaining_from_attributes(
    source_type: str,
    attributes: dict[str, Any] | None,
    now: datetime,
) -> float | None:
    attributes = attributes or {}

    if source_type == "solcast":
        return _sum_future_intervals(attributes.get("detailedForecast"), key="pv_estimate", now=now)

    if source_type in {"open_meteo", "forecast_solar"}:
        wh_period = attributes.get("wh_period")
        if isinstance(wh_period, dict):
            return _sum_future_mapping_kwh(wh_period, now)
        watts = attributes.get("watts")
        if isinstance(watts, dict):
            return _sum_future_mapping_watts(watts, now)

    return None


def _resolve_source_type(
    today_entity: str | None,
    attributes: dict[str, Any] | None,
    configured_source_type: str,
) -> tuple[str, str]:
    if configured_source_type != DEFAULT_SOURCE_TYPE:
        return configured_source_type, "configured_source_type"
    return detect_source_type(today_entity, attributes), "auto_detected"


def _normalize_source_type(value: str | None) -> str:
    value = (value or DEFAULT_SOURCE_TYPE).strip().lower()
    if value not in SOURCE_TYPE_OPTIONS:
        return DEFAULT_SOURCE_TYPE
    return value


def _sum_future_intervals(items: Any, key: str, now: datetime) -> float | None:
    if not isinstance(items, list):
        return None

    total = 0.0
    matched = False
    for item in items:
        if not isinstance(item, dict):
            continue
        period_start = _parse_datetime(item.get("period_start"))
        value = item.get(key)
        if period_start is None or not _is_number(value):
            continue
        if period_start >= now:
            numeric_value = float(value)
            total += numeric_value
            matched = True
    return total if matched else None


def _sum_future_mapping_kwh(values: dict[str, Any], now: datetime) -> float | None:
    total = 0.0
    matched = False
    for key, value in values.items():
        period_start = _parse_datetime(key)
        if period_start is None or not _is_number(value):
            continue
        if period_start >= now:
            total += float(value) / 1000.0
            matched = True
    return total if matched else None


def _sum_future_mapping_watts(values: dict[str, Any], now: datetime) -> float | None:
    entries: list[tuple[datetime, float]] = []
    for key, value in values.items():
        period_start = _parse_datetime(key)
        if period_start is None or not _is_number(value):
            continue
        entries.append((period_start, float(value)))
    entries.sort(key=lambda item: item[0])
    if len(entries) < 2:
        return None

    total_wh = 0.0
    matched = False
    for (period_start, watts), (next_start, _) in zip(entries, entries[1:]):
        if period_start < now:
            continue
        hours = (next_start - period_start).total_seconds() / 3600.0
        total_wh += watts * max(0.0, hours)
        matched = True
    return total_wh / 1000.0 if matched else None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _clean_entity_id(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
