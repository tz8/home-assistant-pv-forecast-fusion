"""Config flow for PV Forecast Fusion."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    CONF_SOURCE_1_BIAS_FACTOR,
    CONF_SOURCE_1_CONFIDENCE,
    CONF_SOURCE_1_NAME,
    CONF_SOURCE_1_REMAINING_ENTITY,
    CONF_SOURCE_1_TODAY_ENTITY,
    CONF_SOURCE_1_TOMORROW_ENTITY,
    CONF_SOURCE_1_TYPE,
    CONF_SOURCE_1_WEIGHT,
    CONF_SOURCE_2_BIAS_FACTOR,
    CONF_SOURCE_2_CONFIDENCE,
    CONF_SOURCE_2_NAME,
    CONF_SOURCE_2_REMAINING_ENTITY,
    CONF_SOURCE_2_TODAY_ENTITY,
    CONF_SOURCE_2_TOMORROW_ENTITY,
    CONF_SOURCE_2_TYPE,
    CONF_SOURCE_2_WEIGHT,
    CONF_SOURCE_3_BIAS_FACTOR,
    CONF_SOURCE_3_CONFIDENCE,
    CONF_SOURCE_3_NAME,
    CONF_SOURCE_3_REMAINING_ENTITY,
    CONF_SOURCE_3_TODAY_ENTITY,
    CONF_SOURCE_3_TOMORROW_ENTITY,
    CONF_SOURCE_3_TYPE,
    CONF_SOURCE_3_WEIGHT,
    DEFAULT_BIAS_FACTOR,
    DEFAULT_CONFIDENCE,
    DEFAULT_NAME,
    DEFAULT_SOURCE_TYPE,
    DEFAULT_WEIGHT,
    DOMAIN,
    SOURCE_TYPE_OPTIONS,
)
from .source_entity_groups import expand_entity_group

_FIELDS: tuple[tuple[str, str, str, str, str, str, str, str], ...] = (
    (
        CONF_SOURCE_1_NAME,
        CONF_SOURCE_1_TYPE,
        CONF_SOURCE_1_TODAY_ENTITY,
        CONF_SOURCE_1_TOMORROW_ENTITY,
        CONF_SOURCE_1_REMAINING_ENTITY,
        CONF_SOURCE_1_WEIGHT,
        CONF_SOURCE_1_BIAS_FACTOR,
        CONF_SOURCE_1_CONFIDENCE,
    ),
    (
        CONF_SOURCE_2_NAME,
        CONF_SOURCE_2_TYPE,
        CONF_SOURCE_2_TODAY_ENTITY,
        CONF_SOURCE_2_TOMORROW_ENTITY,
        CONF_SOURCE_2_REMAINING_ENTITY,
        CONF_SOURCE_2_WEIGHT,
        CONF_SOURCE_2_BIAS_FACTOR,
        CONF_SOURCE_2_CONFIDENCE,
    ),
    (
        CONF_SOURCE_3_NAME,
        CONF_SOURCE_3_TYPE,
        CONF_SOURCE_3_TODAY_ENTITY,
        CONF_SOURCE_3_TOMORROW_ENTITY,
        CONF_SOURCE_3_REMAINING_ENTITY,
        CONF_SOURCE_3_WEIGHT,
        CONF_SOURCE_3_BIAS_FACTOR,
        CONF_SOURCE_3_CONFIDENCE,
    ),
)


def _schema_with_defaults(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    schema: dict[Any, Any] = {
        vol.Required(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)): str,
    }
    for name_key, type_key, today_key, tomorrow_key, remaining_key, weight_key, bias_key, confidence_key in _FIELDS:
        schema[vol.Optional(name_key, default=user_input.get(name_key, ""))] = str
        schema[vol.Optional(type_key, default=user_input.get(type_key, DEFAULT_SOURCE_TYPE))] = vol.In(SOURCE_TYPE_OPTIONS)
        schema[vol.Optional(today_key, default=user_input.get(today_key, ""))] = str
        schema[vol.Optional(tomorrow_key, default=user_input.get(tomorrow_key, ""))] = str
        schema[vol.Optional(remaining_key, default=user_input.get(remaining_key, ""))] = str
        schema[vol.Optional(weight_key, default=user_input.get(weight_key, DEFAULT_WEIGHT))] = vol.Coerce(float)
        schema[vol.Optional(bias_key, default=user_input.get(bias_key, DEFAULT_BIAS_FACTOR))] = vol.Coerce(float)
        schema[vol.Optional(confidence_key, default=user_input.get(confidence_key, DEFAULT_CONFIDENCE))] = vol.Coerce(float)
    return vol.Schema(schema)


class PvForecastFusionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PV Forecast Fusion."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            normalized_input = _normalize_user_input(self.hass, user_input)
            if not any(normalized_input.get(today_key) for _, _, today_key, *_ in _FIELDS):
                errors["base"] = "at_least_one_source"
            else:
                title = normalized_input.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME
                return self.async_create_entry(title=title, data=normalized_input)

        return self.async_show_form(step_id="user", data_schema=_schema_with_defaults(user_input), errors=errors)


def _normalize_user_input(hass, user_input: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(user_input)
    for _, type_key, today_key, tomorrow_key, remaining_key, *_ in _FIELDS:
        today_entities = normalized.get(today_key)
        if not today_entities:
            continue

        today_entity_ids = [item.strip() for item in str(today_entities).split(",") if item.strip()]
        attributes_by_today_entity: dict[str, dict[str, Any] | None] = {}
        for entity_id in today_entity_ids:
            state = hass.states.get(entity_id)
            attributes_by_today_entity[entity_id] = state.attributes if state else None

        resolved_group = expand_entity_group(
            today_entities=today_entities,
            tomorrow_entities=normalized.get(tomorrow_key),
            remaining_entities=normalized.get(remaining_key),
            attributes_by_today_entity=attributes_by_today_entity,
            configured_source_type=normalized.get(type_key),
        )
        if not resolved_group.items:
            continue

        normalized[type_key] = resolved_group.items[0].configured_source_type
        normalized[today_key] = ", ".join(item.today_entity for item in resolved_group.items if item.today_entity)
        normalized[tomorrow_key] = ", ".join(item.tomorrow_entity or "" for item in resolved_group.items).strip(" ,")
        normalized[remaining_key] = ", ".join(item.remaining_entity or "" for item in resolved_group.items).strip(" ,")
    return normalized
