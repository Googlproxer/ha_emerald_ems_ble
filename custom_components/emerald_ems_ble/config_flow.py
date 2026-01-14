from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_PULSES_PER_KWH,
    CONF_PASSKEY,
    DEFAULT_PULSES_PER_KWH,
    DEFAULT_PASSKEY,
)


class EmeraldConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Emerald Energy Advisor over BLE."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: bluetooth.BluetoothServiceInfoBleak | None = None

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle Bluetooth discovery from Home Assistant."""

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery_info = discovery_info

        self.context["title_placeholders"] = {
            "name": discovery_info.name or "Emerald Energy Advisor",
        }

        return await self.async_step_user()

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step initiated by the user."""

        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            title = user_input.get(CONF_NAME) or "Emerald Energy Advisor"
            return self.async_create_entry(title=title, data=user_input)

        # Fetch discovered Bluetooth devices
        discovered_devices = {}
        scanner = bluetooth.async_get_scanner(self.hass)
        for device in scanner.discovered_devices:
            device_name = device.name or "Unknown"
            discovered_devices[device.address] = f"{device_name} ({device.address})"

        # Pre-fill address and name if we have discovery info
        defaults = {}
        if self._discovery_info:
            defaults[CONF_ADDRESS] = self._discovery_info.address
            defaults[CONF_NAME] = self._discovery_info.name or "Emerald Energy Advisor"

        # Build schema with Bluetooth device picker if devices are available
        if discovered_devices:
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS, default=defaults.get(CONF_ADDRESS)): vol.In(discovered_devices),
                    vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, "Emerald Energy Advisor")): str,
                    vol.Required(CONF_PULSES_PER_KWH, default=DEFAULT_PULSES_PER_KWH): vol.All(
                        int, vol.Range(min=1, max=20000)
                    ),
                    vol.Optional(CONF_PASSKEY, default=DEFAULT_PASSKEY): vol.Any(None, int),
                }
            )
        else:
            # Fallback to text input if no devices discovered
            data_schema = vol.Schema(
                {
                    vol.Required(CONF_ADDRESS, default=defaults.get(CONF_ADDRESS)): selector.TextSelector(),
                    vol.Optional(CONF_NAME, default=defaults.get(CONF_NAME, "Emerald Energy Advisor")): str,
                    vol.Required(CONF_PULSES_PER_KWH, default=DEFAULT_PULSES_PER_KWH): vol.All(
                        int, vol.Range(min=1, max=20000)
                    ),
                    vol.Optional(CONF_PASSKEY, default=DEFAULT_PASSKEY): vol.Any(None, int),
                }
            )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )
