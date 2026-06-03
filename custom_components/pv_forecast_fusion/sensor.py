"""Sensor platform for PV Forecast Fusion."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import PvForecastFusionCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = PvForecastFusionCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    async_add_entities(
        [
            PvForecastFusionSensor(entry, coordinator, "today_kwh", "Heute", UnitOfEnergy.KILO_WATT_HOUR),
            PvForecastFusionSensor(entry, coordinator, "tomorrow_kwh", "Morgen", UnitOfEnergy.KILO_WATT_HOUR),
            PvForecastFusionSensor(entry, coordinator, "remaining_today_kwh", "Rest heute", UnitOfEnergy.KILO_WATT_HOUR),
            PvForecastFusionWeatherSensor(entry, coordinator),
        ]
    )


class PvForecastFusionBaseEntity(CoordinatorEntity[PvForecastFusionCoordinator], SensorEntity):
    """Base entity for fusion sensors."""

    _attr_has_entity_name = True

    def __init__(self, entry: ConfigEntry, coordinator: PvForecastFusionCoordinator) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer="Custom",
            model="PV Forecast Fusion",
        )

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        return {
            "sources": data.get("sources", []),
            "active_sources": getattr(data.get("result"), "active_source_names", []),
        }


class PvForecastFusionSensor(PvForecastFusionBaseEntity):
    """Numeric fusion sensor."""

    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 2

    def __init__(
        self,
        entry: ConfigEntry,
        coordinator: PvForecastFusionCoordinator,
        metric_key: str,
        translation_name: str,
        unit: str,
    ) -> None:
        super().__init__(entry, coordinator)
        self._metric_key = metric_key
        self._attr_unique_id = f"{entry.entry_id}_{metric_key}"
        self._attr_name = translation_name
        self._attr_native_unit_of_measurement = unit

    @property
    def native_value(self) -> float | None:
        result = (self.coordinator.data or {}).get("result")
        return getattr(result, self._metric_key, None)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = super().extra_state_attributes
        result = (self.coordinator.data or {}).get("result")
        metric_details = getattr(result, "metric_details", {}).get(self._metric_key)
        if metric_details is not None:
            attrs["contributing_sources"] = metric_details.contributing_sources
            attrs["effective_weights"] = metric_details.effective_weights
        attrs["weather_pattern"] = getattr(result, "weather_pattern", "unknown")
        return attrs


class PvForecastFusionWeatherSensor(PvForecastFusionBaseEntity):
    """Weather pattern from forecast curve shape."""

    _attr_unique_id_suffix = "weather_pattern"
    _attr_icon = "mdi:weather-partly-cloudy"

    def __init__(self, entry: ConfigEntry, coordinator: PvForecastFusionCoordinator) -> None:
        super().__init__(entry, coordinator)
        self._attr_unique_id = f"{entry.entry_id}_weather_pattern"
        self._attr_name = "Wettermuster"

    @property
    def native_value(self) -> str:
        result = (self.coordinator.data or {}).get("result")
        return getattr(result, "weather_pattern", "unknown")
