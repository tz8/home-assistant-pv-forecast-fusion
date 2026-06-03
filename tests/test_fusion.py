from pytest import approx

from custom_components.pv_forecast_fusion.fusion import ForecastSource, classify_weather_pattern, fuse_sources


def test_fuse_sources_combines_bias_weight_and_confidence():
    sources = [
        ForecastSource(name="open_meteo", today_kwh=20.0, tomorrow_kwh=18.0, remaining_today_kwh=8.0, weight=1.0, bias_factor=1.10, confidence=0.8),
        ForecastSource(name="solar_forecast", today_kwh=30.0, tomorrow_kwh=24.0, remaining_today_kwh=12.0, weight=2.0, bias_factor=0.90, confidence=1.0),
    ]

    result = fuse_sources(sources)

    assert result.today_kwh == approx((20.0 * 1.10 * 0.8 + 30.0 * 0.90 * 2.0) / (1.0 * 0.8 + 2.0 * 1.0))
    assert result.tomorrow_kwh == approx((18.0 * 1.10 * 0.8 + 24.0 * 0.90 * 2.0) / (1.0 * 0.8 + 2.0 * 1.0))
    assert result.remaining_today_kwh == approx((8.0 * 1.10 * 0.8 + 12.0 * 0.90 * 2.0) / (1.0 * 0.8 + 2.0 * 1.0))
    assert result.active_source_names == ["open_meteo", "solar_forecast"]


def test_fuse_sources_ignores_missing_values_and_zero_effective_weight():
    sources = [
        ForecastSource(name="valid", today_kwh=24.0, tomorrow_kwh=22.0, remaining_today_kwh=10.0, weight=1.0, bias_factor=1.0, confidence=1.0),
        ForecastSource(name="missing", today_kwh=None, tomorrow_kwh=30.0, remaining_today_kwh=None, weight=5.0, bias_factor=1.0, confidence=1.0),
        ForecastSource(name="disabled", today_kwh=40.0, tomorrow_kwh=40.0, remaining_today_kwh=20.0, weight=0.0, bias_factor=1.0, confidence=1.0),
    ]

    result = fuse_sources(sources)

    assert result.today_kwh == 24.0
    assert result.tomorrow_kwh == approx((22.0 * 1.0 + 30.0 * 5.0) / 6.0)
    assert result.remaining_today_kwh == 10.0
    assert result.active_source_names == ["valid", "missing"]


def test_classify_weather_pattern_detects_sunny_curve():
    curve = [0, 100, 300, 600, 900, 1100, 1200, 1100, 900, 600, 300, 100, 0]
    assert classify_weather_pattern(curve) == "sunny"


def test_classify_weather_pattern_detects_variable_curve():
    curve = [0, 100, 450, 200, 900, 300, 1200, 400, 950, 250, 500, 80, 0]
    assert classify_weather_pattern(curve) == "variable"
