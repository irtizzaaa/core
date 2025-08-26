"""The Multi Serial integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from .const import DOMAIN
from .coordinator import MultiSerialCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

type MultiSerialConfigEntry = ConfigEntry[MultiSerialCoordinator]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Multi Serial component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: MultiSerialConfigEntry) -> bool:
    """Set up Multi Serial from a config entry."""
    
    # Initialize domain data if it doesn't exist
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    
    coordinator = MultiSerialCoordinator(hass, entry.data)
    entry.runtime_data = coordinator
    
    # Store coordinator in domain data
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Start the coordinator
    await coordinator.async_start()
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MultiSerialConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator = entry.runtime_data
    
    # Stop all serial connections
    await coordinator.async_stop()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok and DOMAIN in hass.data:
        if entry.entry_id in hass.data[DOMAIN]:
            del hass.data[DOMAIN][entry.entry_id]
    
    return unload_ok