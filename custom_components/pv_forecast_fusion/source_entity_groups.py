"""Helpers for multi-entity source slots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .source_presets import ResolvedSourceEntities, normalize_source_entities


@dataclass(slots=True)
class ResolvedSourceEntityGroup:
    items: list[ResolvedSourceEntities]


def expand_entity_group(
    today_entities: str | None,
    tomorrow_entities: str | None,
    remaining_entities: str | None,
    attributes_by_today_entity: dict[str, dict[str, Any] | None],
    configured_source_type: str | None = None,
) -> ResolvedSourceEntityGroup:
    today_list = _split_entity_ids(today_entities)
    tomorrow_list = _split_entity_ids(tomorrow_entities)
    remaining_list = _split_entity_ids(remaining_entities)

    items: list[ResolvedSourceEntities] = []
    for index, today_entity in enumerate(today_list):
        items.append(
            normalize_source_entities(
                today_entity=today_entity,
                tomorrow_entity=_entity_at(tomorrow_list, index),
                remaining_entity=_entity_at(remaining_list, index),
                attributes=attributes_by_today_entity.get(today_entity),
                configured_source_type=configured_source_type,
            )
        )

    return ResolvedSourceEntityGroup(items=items)


def aggregate_numeric_values(values: list[float | None]) -> float | None:
    numeric_values = [value for value in values if value is not None]
    if not numeric_values:
        return None
    return sum(numeric_values)


def aggregate_curve_values(curves: list[list[float]]) -> list[float]:
    max_length = max((len(curve) for curve in curves), default=0)
    combined: list[float] = []
    for index in range(max_length):
        combined.append(sum(curve[index] for curve in curves if index < len(curve)))
    return combined


def _split_entity_ids(value: str | None) -> list[str]:
    if not value:
        return []
    parts = [item.strip() for item in value.split(",")]
    while parts and not parts[-1]:
        parts.pop()
    return parts


def _entity_at(values: list[str], index: int) -> str | None:
    if index >= len(values):
        return None
    return values[index] or None
