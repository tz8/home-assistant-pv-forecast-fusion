"""Coordinator for PV Forecast Fusion."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DEFAULT_SCAN_INTERVAL_MINUTES, DOMAIN, SOURCE_SLOTS
from .fusion import ForecastSource, fuse_sources
from .source_parser import extract_curve_values
from .source_presets import derive_remaining_from_attributes
from .source_profile import resolve_related_entities


@dataclass(slots=True)
class SourceSnapshot:
    name: str
    profile: str
    resolution_basis: str
    today_entity: str | None
    tomorrow_entity: str | None
    remaining_entity: str | None
    remaining_method: str | None
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
            logger=None,
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
    today_entity = _entry_value(entry, f"source_{slot}_today_entity")
    explicit_tomorrow_entity = _entry_value(entry, f"source_{slot}_tomorrow_entity")
    explicit_remaining_entity = _entry_value(entry, f"source_{slot}_remaining_entity")
    weight = _float_or_default(_entry_value(entry, f"source_{slot}_weight"), 1.0)
    bias_factor = _float_or_default(_entry_value(entry, f"source_{slot}_bias_factor"), 1.0)
    confidence = _float_or_default(_entry_value(entry, f"source_{slot}_confidence"), 1.0)

    if not today_entity:
        return None, None

    today_state = hass.states.get(today_entity)
    resolved = resolve_related_entities(
        today_entity_id=today_entity,
        attributes=today_state.attributes if today_state else None,
        explicit_tomorrow_entity_id=explicit_tomorrow_entity,
        explicit_remaining_entity_id=explicit_remaining_entity,
    )

    today_state = hass.states.get(resolved.today_entity_id)
    tomorrow_state = hass.states.get(resolved.tomorrow_entity_id) if resolved.tomorrow_entity_id else None
    remaining_state = hass.states.get(resolved.remaining_entity_id) if resolved.remaining_entity_id else None

    today_kwh = _state_to_float(today_state.state if today_state else None)
    tomorrow_kwh = _state_to_float(tomorrow_state.state if tomorrow_state else None)
    remaining_today_kwh = _state_to_float(remaining_state.state if remaining_state else None)
    remaining_method = "direct_sensor" if remaining_today_kwh is not None and resolved.remaining_entity_id else None

    if remaining_today_kwh is None and today_state is not None:
        remaining_today_kwh = derive_remaining_from_attributes(
            source_type=resolved.profile,
            attributes=today_state.attributes,
            now=datetime.now(timezone.utc),
        )
        if remaining_today_kwh is not None:
            remaining_method = "derived_from_today_attributes"

    curve_values = extract_curve_values(today_state.attributes if today_state else None)
    source = ForecastSource(
        name=name,
        today_kwh=today_kwh,
        tomorrow_kwh=tomorrow_kwh,
        remaining_today_kwh=remaining_today_kwh,
        weight=weight,
        bias_factor=bias_factor,
        confidence=confidence,
        curve_values=curve_values,
    )
    snapshot = SourceSnapshot(
        name=name,
        profile=resolved.profile,
        resolution_basis=resolved.resolution_basis,
        today_entity=resolved.today_entity_id,
        tomorrow_entity=resolved.tomorrow_entity_id,
        remaining_entity=resolved.remaining_entity_id,
        remaining_method=remaining_method,
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


def _float_or_default(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
