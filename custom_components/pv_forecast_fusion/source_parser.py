"""Helpers for parsing provider-specific forecast attributes."""

from __future__ import annotations

from typing import Any


def extract_curve_values(attributes: dict[str, Any] | None) -> list[float]:
    if not attributes:
        return []

    watts = attributes.get("watts")
    if isinstance(watts, dict):
        return [float(value) for _, value in sorted(watts.items()) if _is_number(value)]

    detailed_forecast = attributes.get("detailedForecast")
    if isinstance(detailed_forecast, list):
        values: list[float] = []
        for item in detailed_forecast:
            if not isinstance(item, dict):
                continue
            value = item.get("pv_estimate")
            if _is_number(value):
                values.append(float(value))
        return values

    detailed_hourly = attributes.get("detailedHourly")
    if isinstance(detailed_hourly, list):
        values = []
        for item in detailed_hourly:
            if not isinstance(item, dict):
                continue
            value = item.get("pv_estimate")
            if _is_number(value):
                values.append(float(value))
        return values

    wh_period = attributes.get("wh_period")
    if isinstance(wh_period, dict):
        return [float(value) for _, value in sorted(wh_period.items()) if _is_number(value)]

    return []


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
