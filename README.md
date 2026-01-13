# Emerald Energy Advisor (BLE) for Home Assistant

Custom Home Assistant integration that talks to an Emerald Energy Advisor over Bluetooth. The integration now uses the documented BLE protocol (see linked repo) to enable auto-upload and parse 30-second pulse notifications into power readings.

## Features

* Bluetooth discovery hook (local_name matches `Emerald*`).
* Config flow to add the device by address or via discovery, including pulses-per-kWh and optional passkey fields.
* DataUpdateCoordinator-driven polling loop that connects, enables auto-upload, and listens for 30s power notifications.
* Sensor entities for instantaneous power (W) and raw 30s pulse count.
* Diagnostics endpoint returning the latest coordinator data.

## Installation

1. Copy `custom_components/emerald_ems_ble` into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.
3. Add the integration via *Settings → Devices & Services → Add Integration* and search for "Emerald Energy Advisor (BLE)".

## Development notes

* `coordinator.py` now connects over BLE, writes the enable-auto-upload command, waits for a notification on the Time Read characteristic, and parses the 30s pulse payload into watts using the configured pulses-per-kWh. If the device is out of range or does not notify within 8s, the update fails and will retry on the next interval.
* `config_flow.py` supports Bluetooth discovery via Home Assistant's Bluetooth integration and manual address entry; it also accepts `pulses_per_kwh` (default 1000) and an optional 6-digit `passkey` field (stored for future pairing hooks).
* `sensor.py` exposes only the metrics we currently decode from the BLE packets: `power_w` and `pulses_30s`. Extend parsing and entities as new data is decoded.
* `manifest.json` uses placeholder documentation and issue URLs—update them to your project locations.

## Testing locally (syntax only)

You can quickly check for syntax errors:

```bash
python -m compileall custom_components
```

Full Home Assistant tests require the Home Assistant dev container or venv; add them when the BLE client is implemented.
