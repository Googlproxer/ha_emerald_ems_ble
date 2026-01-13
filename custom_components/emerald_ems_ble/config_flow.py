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

    async def async_step_bluetooth(
        self, discovery_info: bluetooth.BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle Bluetooth discovery from Home Assistant."""

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self.context["title_placeholders"] = {
            "name": discovery_info.name or "Emerald Energy Advisor",
        }

        return await self.async_step_user(
            user_input={
                CONF_ADDRESS: discovery_info.address,
                CONF_NAME: discovery_info.name or "Emerald Energy Advisor",
                CONF_PULSES_PER_KWH: DEFAULT_PULSES_PER_KWH,
                CONF_PASSKEY: DEFAULT_PASSKEY,
            }
        )

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Handle the initial step initiated by the user."""

        errors: dict[str, str] = {}

        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()

            title = user_input.get(CONF_NAME) or "Emerald Energy Advisor"
            return self.async_create_entry(title=title, data=user_input)

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ADDRESS): selector.BluetoothSelector(
                    selector.BluetoothSelectorConfig()
                ),
                vol.Optional(CONF_NAME, default="Emerald Energy Advisor"): str,
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
