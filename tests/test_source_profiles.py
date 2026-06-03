from custom_components.pv_forecast_fusion.source_profile import detect_source_profile, resolve_related_entities


def test_detect_source_profile_identifies_solcast_from_attributes():
    profile = detect_source_profile(
        "sensor.solcast_pv_forecast_prognose_heute",
        {"detailedForecast": [{"period_start": "2026-06-04T09:00:00+02:00", "pv_estimate": 0.6}]},
    )

    assert profile == "solcast"


def test_detect_source_profile_identifies_forecast_solar_style_entity():
    profile = detect_source_profile(
        "sensor.hinzenbusch52_energy_production_today",
        {"watts": {"2026-06-04T09:00:00+02:00": 1200}, "wh_period": {"2026-06-04T09:00:00+02:00": 300}},
    )

    assert profile == "forecast_solar"


def test_detect_source_profile_identifies_open_meteo_style_entity_from_name():
    profile = detect_source_profile("sensor.energy_production_today_2", {"friendly_name": "Solar Forecast Garage heute"})

    assert profile == "open_meteo"


def test_resolve_related_entities_for_solcast_today_sensor():
    resolved = resolve_related_entities(
        today_entity_id="sensor.solcast_pv_forecast_prognose_heute",
        attributes={"detailedForecast": [{"period_start": "2026-06-04T09:00:00+02:00", "pv_estimate": 0.6}]},
    )

    assert resolved.profile == "solcast"
    assert resolved.today_entity_id == "sensor.solcast_pv_forecast_prognose_heute"
    assert resolved.tomorrow_entity_id == "sensor.solcast_pv_forecast_prognose_morgen"
    assert resolved.remaining_entity_id is None


def test_resolve_related_entities_for_forecast_solar_today_sensor():
    resolved = resolve_related_entities(
        today_entity_id="sensor.hinzenbusch52_energy_production_today",
        attributes={"watts": {"2026-06-04T09:00:00+02:00": 1200}, "wh_period": {"2026-06-04T09:00:00+02:00": 300}},
    )

    assert resolved.profile == "forecast_solar"
    assert resolved.tomorrow_entity_id == "sensor.hinzenbusch52_energy_production_tomorrow"
    assert resolved.remaining_entity_id == "sensor.hinzenbusch52_energy_production_today_remaining"


def test_resolve_related_entities_for_open_meteo_today_sensor_with_suffix():
    resolved = resolve_related_entities(
        today_entity_id="sensor.energy_production_today_2",
        attributes={"friendly_name": "Solar Forecast Garage heute"},
    )

    assert resolved.profile == "open_meteo"
    assert resolved.tomorrow_entity_id == "sensor.energy_production_tomorrow_2"
    assert resolved.remaining_entity_id == "sensor.energy_production_today_remaining_2"


def test_resolve_related_entities_keeps_explicit_entity_overrides():
    resolved = resolve_related_entities(
        today_entity_id="sensor.energy_production_today",
        attributes={"friendly_name": "Solar Forecast Dach 52 heute"},
        explicit_tomorrow_entity_id="sensor.custom_tomorrow",
        explicit_remaining_entity_id="sensor.custom_remaining",
    )

    assert resolved.tomorrow_entity_id == "sensor.custom_tomorrow"
    assert resolved.remaining_entity_id == "sensor.custom_remaining"
