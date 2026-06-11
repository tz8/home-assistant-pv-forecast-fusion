from datetime import datetime, timezone
from types import SimpleNamespace

from custom_components.pv_forecast_fusion.attributes import build_hourly_forecast_attribute
from custom_components.pv_forecast_fusion.fusion import FusedHourlyForecastPoint


def test_build_hourly_forecast_attribute_serializes_points_for_today() -> None:
    result = SimpleNamespace(
        hourly_details={
            "today_kwh": [
                FusedHourlyForecastPoint(
                    period_start=datetime(2026, 6, 11, 10, tzinfo=timezone.utc),
                    energy_kwh=1.25,
                    contributing_sources=["open_meteo"],
                    effective_weights={"open_meteo": 1.0},
                )
            ]
        }
    )

    hourly_forecast = build_hourly_forecast_attribute("today_kwh", result)

    assert hourly_forecast == [
        {
            "period_start": "2026-06-11T10:00:00+00:00",
            "energy_kwh": 1.25,
            "contributing_sources": ["open_meteo"],
            "effective_weights": {"open_meteo": 1.0},
        }
    ]


def test_build_hourly_forecast_attribute_omits_remaining_today() -> None:
    result = SimpleNamespace(
        hourly_details={
            "remaining_today_kwh": [
                FusedHourlyForecastPoint(
                    period_start=datetime(2026, 6, 11, 11, tzinfo=timezone.utc),
                    energy_kwh=0.75,
                    contributing_sources=["solcast"],
                    effective_weights={"solcast": 2.0},
                )
            ]
        }
    )

    assert build_hourly_forecast_attribute("remaining_today_kwh", result) is None
