from __future__ import annotations

import asyncio
import importlib
import sys
import types
from types import SimpleNamespace


def _install_homeassistant_stubs() -> None:
    if "voluptuous" not in sys.modules:
        voluptuous = types.ModuleType("voluptuous")

        class Marker:
            def __init__(self, key, default=None):
                self.key = key
                self.default = default

            def __hash__(self):
                return hash((self.key, self.default))

            def __eq__(self, other):
                return isinstance(other, Marker) and (self.key, self.default) == (
                    other.key,
                    other.default,
                )

            def __repr__(self):
                return f"Marker(key={self.key!r}, default={self.default!r})"

        class Schema:
            def __init__(self, schema):
                self.schema = schema

        def Required(key, default=None):
            return Marker(key, default)

        def Optional(key, default=None):
            return Marker(key, default)

        def All(*validators):
            return validators

        def Coerce(type_):
            return type_

        def In(values):
            return tuple(values)

        setattr(voluptuous, "Schema", Schema)
        setattr(voluptuous, "Required", Required)
        setattr(voluptuous, "Optional", Optional)
        setattr(voluptuous, "All", All)
        setattr(voluptuous, "Coerce", Coerce)
        setattr(voluptuous, "In", In)
        sys.modules["voluptuous"] = voluptuous

    homeassistant = types.ModuleType("homeassistant")
    config_entries = types.ModuleType("homeassistant.config_entries")
    const = types.ModuleType("homeassistant.const")
    helpers = types.ModuleType("homeassistant.helpers")
    selector = types.ModuleType("homeassistant.helpers.selector")

    class ConfigFlow:
        def __init_subclass__(cls, *, domain=None, **kwargs):
            super().__init_subclass__(**kwargs)
            cls.domain = domain

        def async_show_form(self, *, step_id=None, data_schema=None, errors=None, **kwargs):
            return {
                "type": "form",
                "step_id": step_id,
                "data_schema": data_schema,
                "errors": errors or {},
            }

        def async_create_entry(self, *, title, data):
            return {"type": "create_entry", "title": title, "data": data}

        def async_update_reload_and_abort(self, entry, *, title=None, data=None, **kwargs):
            return {
                "type": "abort",
                "reason": "reconfigure_successful",
                "entry": entry,
                "title": title,
                "data": data,
            }

    class EntitySelectorConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class EntitySelector:
        def __init__(self, config):
            self.config = config

    class NumberSelectorConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class NumberSelector:
        def __init__(self, config):
            self.config = config

    class NumberSelectorMode:
        SLIDER = "slider"

    class Platform:
        SENSOR = "sensor"

    setattr(config_entries, "ConfigFlow", ConfigFlow)
    setattr(const, "CONF_NAME", "name")
    setattr(const, "Platform", Platform)
    setattr(selector, "EntitySelector", EntitySelector)
    setattr(selector, "EntitySelectorConfig", EntitySelectorConfig)
    setattr(selector, "NumberSelector", NumberSelector)
    setattr(selector, "NumberSelectorConfig", NumberSelectorConfig)
    setattr(selector, "NumberSelectorMode", NumberSelectorMode)
    setattr(helpers, "selector", selector)
    setattr(homeassistant, "config_entries", config_entries)
    setattr(homeassistant, "const", const)
    setattr(homeassistant, "helpers", helpers)

    sys.modules.setdefault("homeassistant", homeassistant)
    sys.modules.setdefault("homeassistant.config_entries", config_entries)
    sys.modules.setdefault("homeassistant.const", const)
    sys.modules.setdefault("homeassistant.helpers", helpers)
    sys.modules.setdefault("homeassistant.helpers.selector", selector)


_install_homeassistant_stubs()
config_flow = importlib.import_module("custom_components.pv_forecast_fusion.config_flow")


def test_configured_source_count_uses_highest_populated_slot() -> None:
    count = config_flow._configured_source_count(
        {
            "source_1_today_entity": "sensor.one",
            "source_3_today_entity": "sensor.three",
        }
    )

    assert count == 3
    assert config_flow._configured_source_count({}) == 1


def test_finalize_config_data_removes_deleted_source_slots() -> None:
    data = {
        "name": "Fusion",
        "source_1_today_entity": "sensor.one",
        "source_2_today_entity": "sensor.two",
        "source_3_today_entity": "sensor.three",
        "source_3_weight": 1.0,
        "source_3_bias_factor": 1.0,
        "source_3_confidence": 1.0,
    }

    finalized = config_flow._finalize_config_data(data, 2)

    assert finalized["source_1_today_entity"] == "sensor.one"
    assert finalized["source_2_today_entity"] == "sensor.two"
    assert "source_3_today_entity" not in finalized
    assert "source_3_weight" not in finalized
    assert "source_3_bias_factor" not in finalized
    assert "source_3_confidence" not in finalized


def test_reconfigure_step_prefills_existing_name_and_source_count() -> None:
    flow = config_flow.PvForecastFusionConfigFlow()
    flow._get_reconfigure_entry = lambda: SimpleNamespace(
        title="Bestehend",
        data={
            "name": "Fusion",
            "source_1_today_entity": "sensor.one",
            "source_2_today_entity": "sensor.two",
        },
    )

    result = asyncio.run(flow.async_step_reconfigure())
    schema = result["data_schema"]
    serialized = str(schema.schema)

    assert result["step_id"] == "reconfigure"
    assert flow._source_count == 2
    assert "source_count" in serialized
    assert "name" in serialized


def test_reconfigure_submission_preserves_existing_defaults_until_source_steps() -> None:
    flow = config_flow.PvForecastFusionConfigFlow()
    flow._get_reconfigure_entry = lambda: SimpleNamespace(
        title="Bestehend",
        data={
            "name": "Fusion",
            "source_1_today_entity": "sensor.one",
            "source_2_today_entity": "sensor.two",
        },
    )

    async def fake_next_step():
        return "source-1"

    flow.async_step_source_1 = fake_next_step

    result = asyncio.run(
        flow.async_step_reconfigure({"name": "Neu", "source_count": 1})
    )

    assert result == "source-1"
    assert flow._config_data["name"] == "Neu"
    assert flow._config_data["source_2_today_entity"] == "sensor.two"
    assert flow._source_count == 1
