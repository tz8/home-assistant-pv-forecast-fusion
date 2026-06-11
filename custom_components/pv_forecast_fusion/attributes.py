"""Helpers for serializing entity attributes."""

from __future__ import annotations

from typing import Any


_HOURLY_FORECAST_DISABLED_METRICS = {"remaining_today_kwh"}


def build_hourly_forecast_attribute(metric_key: str, result: Any) -> list[dict[str, Any]] | None:
    """Serialize hourly forecast points for a sensor metric.

    Remaining-today is intentionally omitted because it is a filtered view of today's
    hourly forecast and would only duplicate the same underlying hours.
    """
    if metric_key in _HOURLY_FORECAST_DISABLED_METRICS:
        return None

    hourly_points = getattr(result, "hourly_details", {}).get(metric_key, [])
    if not hourly_points:
        return None

    return [
        {
            "period_start": point.period_start.isoformat(),
            "energy_kwh": point.energy_kwh,
            "contributing_sources": point.contributing_sources,
            "effective_weights": point.effective_weights,
        }
        for point in hourly_points
    ]
