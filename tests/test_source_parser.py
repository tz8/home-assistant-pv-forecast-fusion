from custom_components.pv_forecast_fusion.source_parser import extract_curve_values


def test_extract_curve_values_supports_open_meteo_watts_mapping():
    attributes = {
        "watts": {
            "2026-06-03T09:00:00+02:00": 1200,
            "2026-06-03T09:15:00+02:00": 1500,
            "2026-06-03T09:30:00+02:00": 1100,
        }
    }

    assert extract_curve_values(attributes) == [1200.0, 1500.0, 1100.0]


def test_extract_curve_values_supports_solcast_detailed_forecast():
    attributes = {
        "detailedForecast": [
            {"period_start": "2026-06-03T09:00:00+02:00", "pv_estimate": 0.6},
            {"period_start": "2026-06-03T09:30:00+02:00", "pv_estimate": 0.8},
        ]
    }

    assert extract_curve_values(attributes) == [0.6, 0.8]
