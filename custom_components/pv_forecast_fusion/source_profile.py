"""Detect provider profiles and infer related forecast entities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class ResolvedSourceEntities:
    profile: str
    today_entity_id: str
    tomorrow_entity_id: str | None
    remaining_entity_id: str | None
    resolution_basis: str


def detect_source_profile(entity_id: str, attributes: dict[str, Any] | None) -> str:
    entity_id_lc = entity_id.lower()
    attrs = attributes or {}

    if isinstance(attrs.get("detailedForecast"), list) or isinstance(attrs.get("detailedHourly"), list):
        return "solcast"

    if "solcast" in entity_id_lc:
        return "solcast"

    if "hinzenbusch" in entity_id_lc or ("watts" in attrs and "wh_period" in attrs):
        return "forecast_solar"

    if "energy_production_today" in entity_id_lc:
        return "open_meteo"

    return "generic"


def resolve_related_entities(
    today_entity_id: str,
    attributes: dict[str, Any] | None,
    explicit_tomorrow_entity_id: str | None = None,
    explicit_remaining_entity_id: str | None = None,
) -> ResolvedSourceEntities:
    profile = detect_source_profile(today_entity_id, attributes)
    tomorrow_entity_id = explicit_tomorrow_entity_id or _infer_tomorrow_entity_id(today_entity_id, profile)
    remaining_entity_id = explicit_remaining_entity_id or _infer_remaining_entity_id(today_entity_id, profile)
    resolution_basis = "explicit_override" if explicit_tomorrow_entity_id or explicit_remaining_entity_id else "auto_detected"

    return ResolvedSourceEntities(
        profile=profile,
        today_entity_id=today_entity_id,
        tomorrow_entity_id=tomorrow_entity_id,
        remaining_entity_id=remaining_entity_id,
        resolution_basis=resolution_basis,
    )


def _infer_tomorrow_entity_id(today_entity_id: str, profile: str) -> str | None:
    if profile == "solcast" and today_entity_id.endswith("_heute"):
        return today_entity_id[: -len("_heute")] + "_morgen"

    if today_entity_id.endswith("_today"):
        return today_entity_id[: -len("_today")] + "_tomorrow"

    if "_today_" in today_entity_id:
        return today_entity_id.replace("_today_", "_tomorrow_", 1)

    return None


def _infer_remaining_entity_id(today_entity_id: str, profile: str) -> str | None:
    if profile in {"forecast_solar", "open_meteo"}:
        if today_entity_id.endswith("_today"):
            return today_entity_id + "_remaining"
        if "_today_" in today_entity_id:
            return today_entity_id.replace("_today_", "_today_remaining_", 1)

    return None
