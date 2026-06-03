from datetime import datetime, timezone

from pytest import approx

from custom_components.pv_forecast_fusion.source_presets import (
    derive_remaining_from_attributes,
    detect_source_type,
    normalize_source_entities,
)


def test_detect_source_type_for_live_patterns():
    assert detect_source_type("sensor.solcast_pv_forecast_prognose_heute") == "solcast"
    assert detect_source_type("sensor.energy_production_today") == "forecast_solar"
    assert detect_source_type("sensor.energy_production_today_2") == "forecast_solar"
    assert detect_source_type("sensor.hinzenbusch52_energy_production_today") == "open_meteo"


def test_normalize_source_entities_autofills_forecast_solar_suffix_variants():
    resolved = normalize_source_entities(
        today_entity="sensor.energy_production_today_2",
        tomorrow_entity="",
        remaining_entity="",
        attributes=None,
    )

    assert resolved.source_type == "forecast_solar"
    assert resolved.today_entity == "sensor.energy_production_today_2"
    assert resolved.tomorrow_entity == "sensor.energy_production_tomorrow_2"
    assert resolved.remaining_entity == "sensor.energy_production_today_remaining_2"


def test_normalize_source_entities_autofills_open_meteo_remaining_today():
    resolved = normalize_source_entities(
        today_entity="sensor.hinzenbusch52_energy_production_today",
        tomorrow_entity=None,
        remaining_entity=None,
        attributes={"watts": {"2026-06-03T12:00:00+02:00": 1000}},
    )

    assert resolved.source_type == "open_meteo"
    assert resolved.tomorrow_entity == "sensor.hinzenbusch52_energy_production_tomorrow"
    assert resolved.remaining_entity == "sensor.hinzenbusch52_energy_production_today_remaining"


def test_normalize_source_entities_autofills_solcast_tomorrow_only():
    resolved = normalize_source_entities(
        today_entity="sensor.solcast_pv_forecast_prognose_heute",
        tomorrow_entity=None,
        remaining_entity=None,
        attributes={"detailedForecast": []},
    )

    assert resolved.source_type == "solcast"
    assert resolved.tomorrow_entity == "sensor.solcast_pv_forecast_prognose_morgen"
    assert resolved.remaining_entity is None


def test_derive_remaining_from_solcast_detailed_forecast():
    attributes = {
        "detailedForecast": [
            {"period_start": "2026-06-03T10:00:00+00:00", "pv_estimate": 1.0},
            {"period_start": "2026-06-03T10:30:00+00:00", "pv_estimate": 2.5},
            {"period_start": "2026-06-03T11:00:00+00:00", "pv_estimate": 3.0},
        ]
    }

    remaining = derive_remaining_from_attributes(
        source_type="solcast",
        attributes=attributes,
        now=datetime(2026, 6, 3, 10, 30, tzinfo=timezone.utc),
    )

    assert remaining == approx(5.5)


def test_derive_remaining_from_open_meteo_hourly_wh_period():
    attributes = {
        "wh_period": {
            "2026-06-03T09:00:00+00:00": 100.0,
            "2026-06-03T10:00:00+00:00": 250.0,
            "2026-06-03T11:00:00+00:00": 400.0,
        }
    }

    remaining = derive_remaining_from_attributes(
        source_type="open_meteo",
        attributes=attributes,
        now=datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc),
    )

    assert remaining == approx(0.65)


def test_normalize_source_entities_respects_explicit_source_type_override():
    resolved = normalize_source_entities(
        today_entity="sensor.energy_production_today",
        tomorrow_entity="",
        remaining_entity="",
        attributes={"friendly_name": "Irgendein Forecast"},
        configured_source_type="open_meteo",
    )

    assert resolved.configured_source_type == "open_meteo"
    assert resolved.source_type == "open_meteo"
    assert resolved.resolution_basis == "configured_source_type"
    assert resolved.tomorrow_entity == "sensor.energy_production_tomorrow"
    assert resolved.remaining_entity == "sensor.energy_production_today_remaining"


def test_normalize_source_entities_manual_type_disables_automapping():
    resolved = normalize_source_entities(
        today_entity="sensor.energy_production_today_2",
        tomorrow_entity="",
        remaining_entity="",
        attributes=None,
        configured_source_type="manual",
    )

    assert resolved.configured_source_type == "manual"
    assert resolved.source_type == "manual"
    assert resolved.resolution_basis == "configured_source_type"
    assert resolved.tomorrow_entity is None
    assert resolved.remaining_entity is None
    assert resolved.auto_mapped is False
