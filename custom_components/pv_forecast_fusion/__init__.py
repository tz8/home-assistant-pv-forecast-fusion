"""PV Forecast Fusion integration."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

try:
    from homeassistant.const import Platform
except ModuleNotFoundError:  # pragma: no cover - local unit tests without HA
    Platform = None  # type: ignore[assignment]

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

PLATFORMS: list[Any] = [Platform.SENSOR] if Platform is not None else ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up PV Forecast Fusion from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unloaded
