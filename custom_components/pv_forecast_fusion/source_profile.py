"""Compatibility helpers for source profile detection.

Deprecated in favor of source_presets; kept for tests and transitional callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .source_presets import detect_source_type, normalize_source_entities


@dataclass(slots=True)
class ResolvedSourceEntities:
    profile: str
    today_entity_id: str
    tomorrow_entity_id: str | None
    remaining_entity_id: str | None
    resolution_basis: str


def detect_source_profile(entity_id: str, attributes: dict[str, Any] | None) -> str:
    """Compatibility alias for preset detection."""
    return detect_source_type(entity_id, attributes)


def resolve_related_entities(
    today_entity_id: str,
    attributes: dict[str, Any] | None,
    explicit_tomorrow_entity_id: str | None = None,
    explicit_remaining_entity_id: str | None = None,
) -> ResolvedSourceEntities:
    resolved = normalize_source_entities(
        today_entity=today_entity_id,
        tomorrow_entity=explicit_tomorrow_entity_id,
        remaining_entity=explicit_remaining_entity_id,
        attributes=attributes,
    )
    return ResolvedSourceEntities(
        profile=resolved.source_type,
        today_entity_id=resolved.today_entity,
        tomorrow_entity_id=resolved.tomorrow_entity,
        remaining_entity_id=resolved.remaining_entity,
        resolution_basis=resolved.resolution_basis,
    )
