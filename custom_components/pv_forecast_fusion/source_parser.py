"""Helpers for parsing provider-specific forecast attributes."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from .fusion import HourlyForecastPoint


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


def extract_hourly_energy_forecast(attributes: dict[str, Any] | None) -> list[HourlyForecastPoint]:
    if not attributes:
        return []

    wh_period = attributes.get("wh_period")
    if isinstance(wh_period, dict):
        points: list[HourlyForecastPoint] = []
        for key, value in sorted(wh_period.items()):
            period_start = _parse_datetime(key)
            if period_start is None or not _is_number(value):
                continue
            points.append(HourlyForecastPoint(period_start=period_start, energy_kwh=float(value) / 1000.0))
        return points

    detailed_hourly = attributes.get("detailedHourly")
    if isinstance(detailed_hourly, list):
        points: list[HourlyForecastPoint] = []
        for item in detailed_hourly:
            if not isinstance(item, dict):
                continue
            period_start = _parse_datetime(item.get("period_start"))
            value = item.get("pv_estimate")
            if period_start is None or not _is_number(value):
                continue
            points.append(HourlyForecastPoint(period_start=period_start, energy_kwh=float(value)))
        return points

    detailed_forecast = attributes.get("detailedForecast")
    if isinstance(detailed_forecast, list):
        buckets: dict[datetime, float] = defaultdict(float)
        for item in detailed_forecast:
            if not isinstance(item, dict):
                continue
            period_start = _parse_datetime(item.get("period_start"))
            value = item.get("pv_estimate")
            if period_start is None or not _is_number(value):
                continue
            bucket_start = period_start.replace(minute=0, second=0, microsecond=0)
            buckets[bucket_start] += float(value)
        return [
            HourlyForecastPoint(period_start=period_start, energy_kwh=energy_kwh)
            for period_start, energy_kwh in sorted(buckets.items())
        ]

    return []


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)
