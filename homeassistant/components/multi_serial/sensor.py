"""Sensor platform for Multi Serial integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTR_CONNECTION_STATUS,
    ATTR_ERROR_COUNT,
    ATTR_LAST_READ,
    ATTR_PORT,
    ATTR_READ_COUNT,
    DOMAIN,
)
from .coordinator import MultiSerialCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Multi Serial sensor entities."""
    coordinator: MultiSerialCoordinator = config_entry.runtime_data
    
    entities = []
    
    # Create a sensor for each configured port
    for port_config in coordinator.ports_config:
        port_name = port_config["port_name"]
        entities.append(MultiSerialSensor(coordinator, port_name))
    
    # Create a summary sensor showing total ports and status
    entities.append(MultiSerialSummarySensor(coordinator))
    
    async_add_entities(entities)


class MultiSerialSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Multi Serial sensor for a specific port."""

    _attr_should_poll = False

    def __init__(self, coordinator: MultiSerialCoordinator, port_name: str) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.port_name = port_name
        self._attr_name = f"Serial Port {port_name}"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{port_name}"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        port_data = self.coordinator.get_port_data(self.port_name)
        if port_data:
            return port_data.get("data")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        port_data = self.coordinator.get_port_data(self.port_name)
        if not port_data:
            return {}
        
        return {
            ATTR_PORT: port_data[ATTR_PORT],
            ATTR_CONNECTION_STATUS: port_data[ATTR_CONNECTION_STATUS],
            ATTR_LAST_READ: port_data[ATTR_LAST_READ],
            ATTR_READ_COUNT: port_data[ATTR_READ_COUNT],
            ATTR_ERROR_COUNT: port_data[ATTR_ERROR_COUNT],
            "raw_data": port_data.get("raw_data", ""),
            **port_data.get("attributes", {}),
        }

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        port_data = self.coordinator.get_port_data(self.port_name)
        return port_data is not None and port_data[ATTR_CONNECTION_STATUS] == "connected"


class MultiSerialSummarySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Multi Serial summary sensor."""

    _attr_should_poll = False
    _attr_icon = "mdi:serial-port"

    def __init__(self, coordinator: MultiSerialCoordinator) -> None:
        """Initialize the summary sensor."""
        super().__init__(coordinator)
        self._attr_name = f"{coordinator.config.get('name', 'Multi Serial')} Summary"
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_summary"

    @property
    def native_value(self) -> str:
        """Return the summary state."""
        all_data = self.coordinator.get_all_ports_data()
        
        total_ports = len(all_data)
        connected_ports = sum(
            1 for data in all_data.values() 
            if data[ATTR_CONNECTION_STATUS] == "connected"
        )
        error_ports = sum(
            1 for data in all_data.values() 
            if data[ATTR_CONNECTION_STATUS] == "error"
        )
        
        return f"{connected_ports}/{total_ports} connected"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the summary attributes."""
        all_data = self.coordinator.get_all_ports_data()
        
        total_ports = len(all_data)
        connected_ports = 0
        error_ports = 0
        total_reads = 0
        total_errors = 0
        
        port_status = {}
        
        for port_name, data in all_data.items():
            status = data[ATTR_CONNECTION_STATUS]
            port_status[port_name] = {
                "status": status,
                "read_count": data[ATTR_READ_COUNT],
                "error_count": data[ATTR_ERROR_COUNT],
                "last_read": data[ATTR_LAST_READ],
            }
            
            if status == "connected":
                connected_ports += 1
            elif status == "error":
                error_ports += 1
            
            total_reads += data[ATTR_READ_COUNT]
            total_errors += data[ATTR_ERROR_COUNT]
        
        return {
            "total_ports": total_ports,
            "connected_ports": connected_ports,
            "error_ports": error_ports,
            "total_reads": total_reads,
            "total_errors": total_errors,
            "scan_interval": self.coordinator.scan_interval,
            "ports": port_status,
        }

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        return True  # Summary sensor is always available