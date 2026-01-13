from __future__ import annotations

from datetime import timedelta, datetime
import asyncio
import contextlib
import logging
from typing import Any

from bleak_retry_connector import BleakClientWithServiceCache, establish_connection
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CMD_ENABLE_AUTO_UPLOAD,
    CMD_RETURN_30S_POWER,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_PULSES_PER_KWH,
    DOMAIN,
    READ_CHAR_UUID,
    SERVICE_UUID,
    WRITE_CHAR_UUID,
)

_LOGGER = logging.getLogger(__name__)


class EmeraldBleClient:
    """BLE client for Emerald Energy Advisor using the documented protocol."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        name: str | None = None,
        pulses_per_kwh: int = DEFAULT_PULSES_PER_KWH,
    ) -> None:
        self.hass = hass
        self.address = address
        self.name = name or "Emerald Energy Advisor"
        self.pulses_per_kwh = pulses_per_kwh
        # 30s window -> (3600/30)=120 samples per hour; multiplier yields kW
        self._pulse_multiplier_kw = 120.0 / self.pulses_per_kwh

    async def async_fetch(self) -> dict[str, Any]:
        """Connect, enable uploads, and read a single notification."""

        ble_device = async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if not ble_device:
            raise UpdateFailed("Device not found via Bluetooth; is it in range?")

        disconnect_event = asyncio.Event()

        def _handle_disconnect(client: BleakClientWithServiceCache) -> None:
            disconnect_event.set()

        client = await establish_connection(
            self.hass,
            BleakClientWithServiceCache,
            ble_device,
            ble_device.address,
            disconnect_callback=_handle_disconnect,
            timeout=15,
            use_services_cache=True,
        )

        notification_fut: asyncio.Future[bytes] = asyncio.get_running_loop().create_future()

        def _notification_handler(_handle: int, data: bytearray) -> None:
            if not notification_fut.done():
                notification_fut.set_result(bytes(data))

        try:
            await client.start_notify(READ_CHAR_UUID, _notification_handler)
            await client.write_gatt_char(WRITE_CHAR_UUID, CMD_ENABLE_AUTO_UPLOAD, response=False)

            raw = await asyncio.wait_for(notification_fut, timeout=8)
            return self._parse_payload(raw)
        except asyncio.TimeoutError as err:
            raise UpdateFailed("Timed out waiting for device notification") from err
        except Exception as err:  # pylint: disable=broad-except
            raise UpdateFailed(f"BLE communication failed: {err}") from err
        finally:
            with contextlib.suppress(Exception):
                await client.stop_notify(READ_CHAR_UUID)
            with contextlib.suppress(Exception):
                await client.disconnect()

    def _parse_payload(self, data: bytes) -> dict[str, Any]:
        """Decode Emerald 30s power notification."""

        if len(data) < 11:
            raise UpdateFailed(f"Unexpected payload length {len(data)}")

        header = int.from_bytes(data[0:5], byteorder="big")
        if header != CMD_RETURN_30S_POWER:
            raise UpdateFailed(f"Unsupported command header 0x{header:010x}")

        date_bin = int.from_bytes(data[5:9], byteorder="big")
        pulses = int.from_bytes(data[9:11], byteorder="big")

        power_kw = pulses * self._pulse_multiplier_kw
        power_w = power_kw * 1000.0

        # Decode timestamp (6 bits sec, 6 bits min, 5 bits hour, 5 bits day, 4 bits month, 6 bits year offset 2000)
        year = 2000 + (date_bin >> 26)
        month = (date_bin >> 22) & 0x0F
        day = (date_bin >> 17) & 0x1F
        hour = (date_bin >> 12) & 0x1F
        minute = (date_bin >> 6) & 0x3F
        second = date_bin & 0x3F

        try:
            ts = dt_util.as_utc(datetime(year, month, day, hour, minute, second))
        except Exception:  # date may be invalid; fallback to now
            ts = dt_util.utcnow()

        return {
            "power_w": round(power_w, 2),
            "pulses_30s": pulses,
            "timestamp": ts.isoformat(),
        }


class EmeraldDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage BLE polling for Emerald Energy Advisor."""

    def __init__(
        self,
        hass: HomeAssistant,
        address: str,
        name: str | None = None,
        pulses_per_kwh: int = DEFAULT_PULSES_PER_KWH,
    ) -> None:
        self.client = EmeraldBleClient(
            hass=hass,
            address=address,
            name=name,
            pulses_per_kwh=pulses_per_kwh,
        )
        self.device_name = self.client.name

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_POLL_INTERVAL),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.client.async_fetch()
        except Exception as err:  # pylint: disable=broad-except
            raise UpdateFailed(
                f"Error communicating with Emerald Energy Advisor: {err}"
            ) from err

    async def async_shutdown(self) -> None:
        """Release resources on unload."""
        # client disconnects after each fetch; nothing persistent to close
        return None
