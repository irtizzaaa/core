"""Config flow for Multi Serial integration."""

from __future__ import annotations

import logging
from typing import Any

import serial.tools.list_ports
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import (
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
    DEFAULT_BAUDRATE,
    DEFAULT_BYTESIZE,
    DEFAULT_DSRDTR,
    DEFAULT_PARITY,
    DEFAULT_RTSCTS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STOPBITS,
    DEFAULT_TIMEOUT,
    DEFAULT_XONXOFF,
    DOMAIN,
    MAX_SIMULTANEOUS_PORTS,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default="Multi Serial Scanner"): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=60.0)
        ),
    }
)

STEP_PORT_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PORT_NAME): str,
        vol.Optional(CONF_BAUDRATE, default=DEFAULT_BAUDRATE): vol.All(
            vol.Coerce(int), vol.Range(min=300, max=115200)
        ),
        vol.Optional(CONF_BYTESIZE, default=DEFAULT_BYTESIZE): vol.In([5, 6, 7, 8]),
        vol.Optional(CONF_PARITY, default=DEFAULT_PARITY): vol.In(["N", "E", "O", "M", "S"]),
        vol.Optional(CONF_STOPBITS, default=DEFAULT_STOPBITS): vol.In([1, 1.5, 2]),
        vol.Optional(CONF_XONXOFF, default=DEFAULT_XONXOFF): bool,
        vol.Optional(CONF_RTSCTS, default=DEFAULT_RTSCTS): bool,
        vol.Optional(CONF_DSRDTR, default=DEFAULT_DSRDTR): bool,
        vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): vol.All(
            vol.Coerce(float), vol.Range(min=0.1, max=10.0)
        ),
    }
)


def get_available_ports() -> list[str]:
    """Get list of available serial ports."""
    # Return empty list to avoid blocking I/O in event loop
    # Users can manually enter port names
    return []


class MultiSerialConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Multi Serial."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        super().__init__()
        self.ports_config: list[dict[str, Any]] = []
        self.name: str = ""

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={
                    "max_ports": str(MAX_SIMULTANEOUS_PORTS),
                },
            )

        self.name = user_input[CONF_NAME]
        self.scan_interval = user_input[CONF_SCAN_INTERVAL]

        return await self.async_step_port()

    async def async_step_port(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding a serial port."""
        available_ports = get_available_ports()
        
        if user_input is None:
            # Always allow manual entry since auto-detection is disabled
            schema = STEP_PORT_DATA_SCHEMA.extend(
                {
                    vol.Required(CONF_PORT_NAME): str,
                }
            )
            description = "Enter port name manually (e.g., COM3, /dev/ttyUSB0, /dev/ttyS0)"
            
            return self.async_show_form(
                step_id="port",
                data_schema=schema,
                description_placeholders={
                    "available_ports": description,
                    "current_ports": str(len(self.ports_config)),
                    "max_ports": str(MAX_SIMULTANEOUS_PORTS),
                },
            )

        # Check if port is already configured
        if any(port[CONF_PORT_NAME] == user_input[CONF_PORT_NAME] for port in self.ports_config):
            return self.async_show_form(
                step_id="port",
                data_schema=STEP_PORT_DATA_SCHEMA,
                errors={"base": "port_already_configured"},
            )

        # Check maximum ports limit
        if len(self.ports_config) >= MAX_SIMULTANEOUS_PORTS:
            return self.async_show_form(
                step_id="port",
                data_schema=STEP_PORT_DATA_SCHEMA,
                errors={"base": "max_ports_exceeded"},
            )

        self.ports_config.append(user_input)

        # Ask if user wants to add more ports
        return await self.async_step_add_more()

    async def async_step_add_more(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask if user wants to add more ports."""
        if user_input is None:
            return self.async_show_form(
                step_id="add_more",
                data_schema=vol.Schema(
                    {
                        vol.Required("add_more", default=True): bool,
                    }
                ),
                description_placeholders={
                    "current_ports": str(len(self.ports_config)),
                    "max_ports": str(MAX_SIMULTANEOUS_PORTS),
                },
            )

        if user_input["add_more"] and len(self.ports_config) < MAX_SIMULTANEOUS_PORTS:
            return await self.async_step_port()

        # Create the config entry
        config_data = {
            CONF_NAME: self.name,
            CONF_SCAN_INTERVAL: self.scan_interval,
            CONF_PORTS: self.ports_config,
        }

        return self.async_create_entry(
            title=self.name,
            data=config_data,
        )

    async def async_step_import(self, import_data: dict[str, Any]) -> FlowResult:
        """Handle import from configuration.yaml."""
        return await self.async_step_user(import_data)