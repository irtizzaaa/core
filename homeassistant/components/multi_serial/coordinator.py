"""Data coordinator for Multi Serial integration."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any

import serial_asyncio
from serial import SerialException

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ATTR_CONNECTION_STATUS,
    ATTR_ERROR_COUNT,
    ATTR_LAST_READ,
    ATTR_PORT,
    ATTR_READ_COUNT,
    CONF_BAUDRATE,
    CONF_BYTESIZE,
    CONF_DSRDTR,
    CONF_PARITY,
    CONF_PORTS,
    CONF_PORT_NAME,
    CONF_RTSCTS,
    CONF_SCAN_INTERVAL,
    CONF_STOPBITS,
    CONF_TIMEOUT,
    CONF_XONXOFF,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class MultiSerialCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from multiple serial ports."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        self.config = config
        self.ports_config = config[CONF_PORTS]
        self.scan_interval = config[CONF_SCAN_INTERVAL]
        
        # Initialize port data
        self.port_data: dict[str, dict[str, Any]] = {}
        self.port_tasks: dict[str, asyncio.Task] = {}
        self.port_readers: dict[str, asyncio.StreamReader] = {}
        self.port_writers: dict[str, asyncio.StreamWriter] = {}
        
        for port_config in self.ports_config:
            port_name = port_config[CONF_PORT_NAME]
            self.port_data[port_name] = {
                ATTR_PORT: port_name,
                "data": None,
                ATTR_LAST_READ: None,
                ATTR_READ_COUNT: 0,
                ATTR_ERROR_COUNT: 0,
                ATTR_CONNECTION_STATUS: "disconnected",
                "raw_data": "",
                "attributes": {},
            }

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=self.scan_interval),
        )

    async def async_start(self) -> None:
        """Start all serial port connections."""
        _LOGGER.info("Starting Multi Serial coordinator with %d ports", len(self.ports_config))
        
        for port_config in self.ports_config:
            port_name = port_config[CONF_PORT_NAME]
            try:
                await self._connect_port(port_config)
            except Exception as err:
                _LOGGER.error("Failed to connect to port %s: %s", port_name, err)
                self.port_data[port_name][ATTR_CONNECTION_STATUS] = "error"
                self.port_data[port_name][ATTR_ERROR_COUNT] += 1

    async def async_stop(self) -> None:
        """Stop all serial port connections."""
        _LOGGER.info("Stopping Multi Serial coordinator")
        
        # Cancel all port tasks
        for task in self.port_tasks.values():
            if not task.done():
                task.cancel()
        
        # Close all connections
        for writer in self.port_writers.values():
            if not writer.is_closing():
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass
        
        # Wait for tasks to complete
        if self.port_tasks:
            await asyncio.gather(*self.port_tasks.values(), return_exceptions=True)

    async def _connect_port(self, port_config: dict[str, Any]) -> None:
        """Connect to a single serial port."""
        port_name = port_config[CONF_PORT_NAME]
        
        try:
            reader, writer = await serial_asyncio.open_serial_connection(
                url=port_name,
                baudrate=port_config[CONF_BAUDRATE],
                bytesize=port_config[CONF_BYTESIZE],
                parity=port_config[CONF_PARITY],
                stopbits=port_config[CONF_STOPBITS],
                xonxoff=port_config[CONF_XONXOFF],
                rtscts=port_config[CONF_RTSCTS],
                dsrdtr=port_config[CONF_DSRDTR],
                timeout=port_config[CONF_TIMEOUT],
            )
            
            self.port_readers[port_name] = reader
            self.port_writers[port_name] = writer
            self.port_data[port_name][ATTR_CONNECTION_STATUS] = "connected"
            
            # Start reading task for this port
            self.port_tasks[port_name] = asyncio.create_task(
                self._read_port_data(port_name, reader)
            )
            
            _LOGGER.info("Connected to serial port: %s", port_name)
            
        except SerialException as err:
            _LOGGER.error("Serial connection error for port %s: %s", port_name, err)
            self.port_data[port_name][ATTR_CONNECTION_STATUS] = "error"
            self.port_data[port_name][ATTR_ERROR_COUNT] += 1
            raise

    async def _read_port_data(self, port_name: str, reader: asyncio.StreamReader) -> None:
        """Read data from a serial port continuously."""
        _LOGGER.debug("Starting to read from port: %s", port_name)
        
        while True:
            try:
                # Read a line from the serial port
                line = await reader.readline()
                
                if not line:
                    _LOGGER.warning("No data received from port %s, connection may be lost", port_name)
                    break
                
                # Decode the line
                try:
                    data_str = line.decode("utf-8").strip()
                except UnicodeDecodeError:
                    data_str = line.decode("latin-1").strip()
                
                if data_str:
                    # Update port data
                    self.port_data[port_name]["raw_data"] = data_str
                    self.port_data[port_name]["data"] = data_str
                    self.port_data[port_name][ATTR_LAST_READ] = datetime.now().isoformat()
                    self.port_data[port_name][ATTR_READ_COUNT] += 1
                    
                    # Try to parse as JSON for attributes
                    try:
                        json_data = json.loads(data_str)
                        if isinstance(json_data, dict):
                            self.port_data[port_name]["attributes"] = json_data
                    except (json.JSONDecodeError, TypeError):
                        # Not JSON, keep as string
                        pass
                    
                    _LOGGER.debug("Received from %s: %s", port_name, data_str)
                    
                    # Notify listeners of data update
                    self.async_set_updated_data(self.port_data)
                
            except asyncio.CancelledError:
                _LOGGER.debug("Read task cancelled for port: %s", port_name)
                break
            except Exception as err:
                _LOGGER.error("Error reading from port %s: %s", port_name, err)
                self.port_data[port_name][ATTR_ERROR_COUNT] += 1
                self.port_data[port_name][ATTR_CONNECTION_STATUS] = "error"
                
                # Wait before retrying
                await asyncio.sleep(5)
                
                # Try to reconnect
                try:
                    port_config = next(
                        config for config in self.ports_config 
                        if config[CONF_PORT_NAME] == port_name
                    )
                    await self._connect_port(port_config)
                    break
                except Exception as reconnect_err:
                    _LOGGER.error("Failed to reconnect to port %s: %s", port_name, reconnect_err)
                    await asyncio.sleep(10)

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data from all ports."""
        # The actual data updates happen in the _read_port_data tasks
        # This method is called by the coordinator's update mechanism
        return self.port_data

    def get_port_data(self, port_name: str) -> dict[str, Any] | None:
        """Get data for a specific port."""
        return self.port_data.get(port_name)

    def get_all_ports_data(self) -> dict[str, Any]:
        """Get data for all ports."""
        return self.port_data