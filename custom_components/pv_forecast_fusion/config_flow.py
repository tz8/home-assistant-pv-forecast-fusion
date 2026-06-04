"""Config flow for PV Forecast Fusion."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers import selector

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
    SOURCE_SLOTS,
    SOURCE_TYPE_OPTIONS,
)
from .source_entity_groups import expand_entity_group

CONF_SOURCE_COUNT = "source_count"

FORM_SOURCE_NAME = "source_name"
FORM_SOURCE_TYPE = "source_type"
FORM_SOURCE_TODAY_ENTITY = "source_today_entity"
FORM_SOURCE_TOMORROW_ENTITY = "source_tomorrow_entity"
FORM_SOURCE_REMAINING_ENTITY = "source_remaining_entity"
FORM_SOURCE_TOMORROW_ENTITY_CSV = "source_tomorrow_entity_csv"
FORM_SOURCE_REMAINING_ENTITY_CSV = "source_remaining_entity_csv"
FORM_SOURCE_INFLUENCE = "source_influence"
FORM_SOURCE_ADJUSTMENT_PERCENT = "source_adjustment_percent"


@dataclass(frozen=True, slots=True)
class SourceFieldSet:
    slot: int
    name_key: str
    type_key: str
    today_key: str
    tomorrow_key: str
    remaining_key: str
    weight_key: str
    bias_key: str
    confidence_key: str


_SOURCE_FIELDS_BY_SLOT: dict[int, SourceFieldSet] = {
    1: SourceFieldSet(
        slot=1,
        name_key=CONF_SOURCE_1_NAME,
        type_key=CONF_SOURCE_1_TYPE,
        today_key=CONF_SOURCE_1_TODAY_ENTITY,
        tomorrow_key=CONF_SOURCE_1_TOMORROW_ENTITY,
        remaining_key=CONF_SOURCE_1_REMAINING_ENTITY,
        weight_key=CONF_SOURCE_1_WEIGHT,
        bias_key=CONF_SOURCE_1_BIAS_FACTOR,
        confidence_key=CONF_SOURCE_1_CONFIDENCE,
    ),
    2: SourceFieldSet(
        slot=2,
        name_key=CONF_SOURCE_2_NAME,
        type_key=CONF_SOURCE_2_TYPE,
        today_key=CONF_SOURCE_2_TODAY_ENTITY,
        tomorrow_key=CONF_SOURCE_2_TOMORROW_ENTITY,
        remaining_key=CONF_SOURCE_2_REMAINING_ENTITY,
        weight_key=CONF_SOURCE_2_WEIGHT,
        bias_key=CONF_SOURCE_2_BIAS_FACTOR,
        confidence_key=CONF_SOURCE_2_CONFIDENCE,
    ),
    3: SourceFieldSet(
        slot=3,
        name_key=CONF_SOURCE_3_NAME,
        type_key=CONF_SOURCE_3_TYPE,
        today_key=CONF_SOURCE_3_TODAY_ENTITY,
        tomorrow_key=CONF_SOURCE_3_TOMORROW_ENTITY,
        remaining_key=CONF_SOURCE_3_REMAINING_ENTITY,
        weight_key=CONF_SOURCE_3_WEIGHT,
        bias_key=CONF_SOURCE_3_BIAS_FACTOR,
        confidence_key=CONF_SOURCE_3_CONFIDENCE,
    ),
}


def _build_intro_schema(user_input: dict[str, Any] | None = None) -> vol.Schema:
    user_input = user_input or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=user_input.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(
                CONF_SOURCE_COUNT,
                default=int(user_input.get(CONF_SOURCE_COUNT, 1)),
            ): vol.All(vol.Coerce(int), vol.In(list(SOURCE_SLOTS))),
        }
    )


def _build_source_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    defaults = defaults or {}
    schema: dict[Any, Any] = {
        vol.Optional(FORM_SOURCE_NAME, default=defaults.get(FORM_SOURCE_NAME, "")): str,
        vol.Optional(
            FORM_SOURCE_TYPE,
            default=defaults.get(FORM_SOURCE_TYPE, DEFAULT_SOURCE_TYPE),
        ): vol.In(SOURCE_TYPE_OPTIONS),
        vol.Required(
            FORM_SOURCE_TODAY_ENTITY,
            default=defaults.get(FORM_SOURCE_TODAY_ENTITY, []),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="sensor",
                multiple=True,
            )
        ),
        vol.Optional(
            FORM_SOURCE_TOMORROW_ENTITY,
            default=defaults.get(FORM_SOURCE_TOMORROW_ENTITY, []),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="sensor",
                multiple=True,
            )
        ),
        vol.Optional(
            FORM_SOURCE_TOMORROW_ENTITY_CSV,
            default=defaults.get(FORM_SOURCE_TOMORROW_ENTITY_CSV, ""),
        ): str,
        vol.Optional(
            FORM_SOURCE_REMAINING_ENTITY,
            default=defaults.get(FORM_SOURCE_REMAINING_ENTITY, []),
        ): selector.EntitySelector(
            selector.EntitySelectorConfig(
                domain="sensor",
                multiple=True,
            )
        ),
        vol.Optional(
            FORM_SOURCE_REMAINING_ENTITY_CSV,
            default=defaults.get(FORM_SOURCE_REMAINING_ENTITY_CSV, ""),
        ): str,
    }

    schema[
        vol.Optional(
            FORM_SOURCE_INFLUENCE,
            default=defaults.get(FORM_SOURCE_INFLUENCE, DEFAULT_WEIGHT * DEFAULT_CONFIDENCE),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=0.0,
            max=2.0,
            step=0.05,
            mode=selector.NumberSelectorMode.SLIDER,
        )
    )
    schema[
        vol.Optional(
            FORM_SOURCE_ADJUSTMENT_PERCENT,
            default=defaults.get(FORM_SOURCE_ADJUSTMENT_PERCENT, 0.0),
        )
    ] = selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=-100.0,
            max=100.0,
            step=1.0,
            mode=selector.NumberSelectorMode.SLIDER,
            unit_of_measurement="%",
        )
    )

    return vol.Schema(schema)


class PvForecastFusionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for PV Forecast Fusion."""

    VERSION = 1

    def __init__(self) -> None:
        self._config_data: dict[str, Any] = {}
        self._source_count = 1
        self._reconfigure_entry = None

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            title = str(user_input.get(CONF_NAME, DEFAULT_NAME)).strip() or DEFAULT_NAME
            self._config_data = {CONF_NAME: title}
            self._source_count = int(user_input.get(CONF_SOURCE_COUNT, 1))
            self._reconfigure_entry = None
            return await self.async_step_source_1()

        return self.async_show_form(
            step_id="user",
            data_schema=_build_intro_schema(user_input),
            errors=errors,
        )

    async def async_step_reconfigure(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            title = str(user_input.get(CONF_NAME, DEFAULT_NAME)).strip() or DEFAULT_NAME
            self._config_data = dict(entry.data)
            self._config_data[CONF_NAME] = title
            self._source_count = int(user_input.get(CONF_SOURCE_COUNT, 1))
            self._reconfigure_entry = entry
            return await self.async_step_source_1()

        self._config_data = dict(entry.data)
        self._source_count = _configured_source_count(self._config_data)
        self._reconfigure_entry = entry
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_build_intro_schema(
                {
                    CONF_NAME: entry.title or entry.data.get(CONF_NAME, DEFAULT_NAME),
                    CONF_SOURCE_COUNT: self._source_count,
                }
            ),
            errors=errors,
        )

    async def async_step_source_1(self, user_input: dict[str, Any] | None = None):
        return await self._async_step_source(_SOURCE_FIELDS_BY_SLOT[1], user_input)

    async def async_step_source_2(self, user_input: dict[str, Any] | None = None):
        return await self._async_step_source(_SOURCE_FIELDS_BY_SLOT[2], user_input)

    async def async_step_source_3(self, user_input: dict[str, Any] | None = None):
        return await self._async_step_source(_SOURCE_FIELDS_BY_SLOT[3], user_input)

    async def _async_step_source(
        self,
        fields: SourceFieldSet,
        user_input: dict[str, Any] | None = None,
    ):
        errors: dict[str, str] = {}

        if user_input is not None:
            mapped_input = _map_source_form_to_config(fields, user_input)
            if not mapped_input[fields.today_key]:
                errors["base"] = "source_today_required"
            else:
                self._config_data.update(_normalize_source_input(self.hass, fields, mapped_input))
                if fields.slot >= self._source_count:
                    title = self._config_data.get(CONF_NAME, DEFAULT_NAME)
                    final_data = _finalize_config_data(self._config_data, self._source_count)
                    if self._reconfigure_entry is not None:
                        return self.async_update_reload_and_abort(
                            self._reconfigure_entry,
                            title=title,
                            data=final_data,
                        )
                    return self.async_create_entry(title=title, data=final_data)
                return await getattr(self, f"async_step_source_{fields.slot + 1}")()

        return self.async_show_form(
            step_id=f"source_{fields.slot}",
            data_schema=_build_source_schema(
                user_input or _source_form_defaults_from_config(self._config_data, fields)
            ),
            errors=errors,
        )


def _source_form_defaults_from_config(
    config_data: dict[str, Any],
    fields: SourceFieldSet,
) -> dict[str, Any]:
    weight = _coerce_float(config_data.get(fields.weight_key), DEFAULT_WEIGHT)
    confidence = _coerce_float(config_data.get(fields.confidence_key), DEFAULT_CONFIDENCE)
    bias_factor = _coerce_float(config_data.get(fields.bias_key), DEFAULT_BIAS_FACTOR)
    return {
        FORM_SOURCE_NAME: config_data.get(fields.name_key, ""),
        FORM_SOURCE_TYPE: config_data.get(fields.type_key, DEFAULT_SOURCE_TYPE),
        FORM_SOURCE_TODAY_ENTITY: _csv_to_entity_selector_value(config_data.get(fields.today_key)),
        FORM_SOURCE_TOMORROW_ENTITY: _csv_to_entity_selector_value(config_data.get(fields.tomorrow_key)),
        FORM_SOURCE_REMAINING_ENTITY: _csv_to_entity_selector_value(config_data.get(fields.remaining_key)),
        FORM_SOURCE_TOMORROW_ENTITY_CSV: _csv_with_inner_placeholders_or_empty(
            config_data.get(fields.tomorrow_key)
        ),
        FORM_SOURCE_REMAINING_ENTITY_CSV: _csv_with_inner_placeholders_or_empty(
            config_data.get(fields.remaining_key)
        ),
        FORM_SOURCE_INFLUENCE: weight * confidence,
        FORM_SOURCE_ADJUSTMENT_PERCENT: _bias_factor_to_adjustment_percent(bias_factor),
    }


def _configured_source_count(config_data: dict[str, Any]) -> int:
    configured_slots = [
        slot
        for slot, fields in _SOURCE_FIELDS_BY_SLOT.items()
        if str(config_data.get(fields.today_key, "")).strip()
    ]
    if not configured_slots:
        return 1
    return max(configured_slots)


def _finalize_config_data(config_data: dict[str, Any], source_count: int) -> dict[str, Any]:
    finalized = dict(config_data)
    for slot, fields in _SOURCE_FIELDS_BY_SLOT.items():
        if slot <= source_count:
            continue
        for key in (
            fields.name_key,
            fields.type_key,
            fields.today_key,
            fields.tomorrow_key,
            fields.remaining_key,
            fields.weight_key,
            fields.bias_key,
            fields.confidence_key,
        ):
            finalized.pop(key, None)
    return finalized


def _map_source_form_to_config(
    fields: SourceFieldSet,
    user_input: dict[str, Any],
) -> dict[str, Any]:
    influence = min(
        2.0,
        max(0.0, _coerce_float(user_input.get(FORM_SOURCE_INFLUENCE), DEFAULT_WEIGHT * DEFAULT_CONFIDENCE)),
    )
    adjustment_percent = min(
        100.0,
        max(-100.0, _coerce_float(user_input.get(FORM_SOURCE_ADJUSTMENT_PERCENT), 0.0)),
    )
    return {
        fields.name_key: str(user_input.get(FORM_SOURCE_NAME, "")).strip(),
        fields.type_key: user_input.get(FORM_SOURCE_TYPE, DEFAULT_SOURCE_TYPE),
        fields.today_key: _selector_value_to_entity_csv(user_input.get(FORM_SOURCE_TODAY_ENTITY)),
        fields.tomorrow_key: _csv_override_or_selector_value(
            user_input.get(FORM_SOURCE_TOMORROW_ENTITY_CSV),
            user_input.get(FORM_SOURCE_TOMORROW_ENTITY),
        ),
        fields.remaining_key: _csv_override_or_selector_value(
            user_input.get(FORM_SOURCE_REMAINING_ENTITY_CSV),
            user_input.get(FORM_SOURCE_REMAINING_ENTITY),
        ),
        fields.weight_key: influence,
        fields.bias_key: _adjustment_percent_to_bias_factor(adjustment_percent),
        fields.confidence_key: 1.0,
    }


def _normalize_source_input(
    hass,
    fields: SourceFieldSet,
    source_input: dict[str, Any],
) -> dict[str, Any]:
    normalized = dict(source_input)
    today_entities = normalized.get(fields.today_key)
    if not today_entities:
        return normalized

    today_entity_ids = [item.strip() for item in str(today_entities).split(",") if item.strip()]
    attributes_by_today_entity: dict[str, dict[str, Any] | None] = {}
    for entity_id in today_entity_ids:
        state = hass.states.get(entity_id)
        attributes_by_today_entity[entity_id] = state.attributes if state else None

    resolved_group = expand_entity_group(
        today_entities=today_entities,
        tomorrow_entities=normalized.get(fields.tomorrow_key),
        remaining_entities=normalized.get(fields.remaining_key),
        attributes_by_today_entity=attributes_by_today_entity,
        configured_source_type=normalized.get(fields.type_key),
    )
    if not resolved_group.items:
        return normalized

    normalized[fields.type_key] = resolved_group.items[0].configured_source_type
    normalized[fields.today_key] = _join_entity_ids(
        item.today_entity for item in resolved_group.items if item.today_entity
    )
    normalized[fields.tomorrow_key] = _join_entity_ids(
        item.tomorrow_entity or "" for item in resolved_group.items
    )
    normalized[fields.remaining_key] = _join_entity_ids(
        item.remaining_entity or "" for item in resolved_group.items
    )
    return normalized


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _adjustment_percent_to_bias_factor(adjustment_percent: float) -> float:
    return 1.0 + (float(adjustment_percent) / 100.0)


def _bias_factor_to_adjustment_percent(bias_factor: float) -> float:
    return (float(bias_factor) - 1.0) * 100.0


def _join_entity_ids(values: Iterable[str]) -> str:
    parts = [str(value).strip() for value in values]
    while parts and not parts[-1]:
        parts.pop()
    return ", ".join(parts)


def _csv_to_entity_selector_value(value: Any) -> list[str]:
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _selector_value_to_entity_csv(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def _csv_override_or_selector_value(csv_override: Any, selector_value: Any) -> str:
    override = str(csv_override or "").strip()
    if override:
        return override
    return _selector_value_to_entity_csv(selector_value)


def _csv_with_inner_placeholders_or_empty(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    parts = [item.strip() for item in raw.split(",")]
    if any(not item for item in parts[:-1]):
        return raw
    return ""
