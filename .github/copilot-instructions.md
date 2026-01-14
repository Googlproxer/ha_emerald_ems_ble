# Emerald Energy Advisor (BLE) - Copilot Instructions

## Project Overview

This is a custom Home Assistant integration that communicates with Emerald Energy Advisor devices over Bluetooth Low Energy (BLE). The integration uses the documented BLE protocol to enable auto-upload and parse 30-second pulse notifications into power readings.

**Key Features:**
- Bluetooth discovery for devices with local_name matching `Emerald*`
- Config flow for adding devices (by address or discovery)
- DataUpdateCoordinator-driven polling with BLE connection management
- Sensor entities for instantaneous power (W) and raw 30s pulse count
- Diagnostics endpoint for troubleshooting

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** Home Assistant Core
- **Key Dependencies:**
  - `bleak` and `bleak-retry-connector` for BLE communication
  - Home Assistant's `bluetooth` component for device discovery
  - `DataUpdateCoordinator` for state management
- **Testing:** Basic syntax validation via `python -m compileall`

## Project Structure

```
custom_components/emerald_ems_ble/
├── __init__.py           # Integration setup and entry point
├── config_flow.py        # Configuration flow for device setup
├── const.py              # Constants (UUIDs, commands, defaults)
├── coordinator.py        # BLE client and DataUpdateCoordinator
├── diagnostics.py        # Diagnostics data provider
├── manifest.json         # Integration metadata
├── sensor.py             # Sensor entities (power_w, pulses_30s)
└── strings.json          # Localized strings for UI

tests/
├── __init__.py
└── test_const.py         # Basic constant tests
```

## Coding Standards

### Python Style
- Use Python 3.11+ type hints (e.g., `str | None` instead of `Optional[str]`)
- Import `from __future__ import annotations` at the top of each file
- Follow Home Assistant's coding standards and patterns
- Use `_LOGGER = logging.getLogger(__name__)` for logging
- Prefer `async`/`await` for I/O operations

### Home Assistant Patterns
- Use `ConfigEntry` for integration configuration
- Implement `DataUpdateCoordinator` for polling/updates
- Use `async_ble_device_from_address` from `homeassistant.components.bluetooth`
- Follow Home Assistant's entity naming conventions
- Use `DOMAIN` constant from `const.py` for all domain references

### BLE Protocol
- Service UUID: `00001910-0000-1000-8000-00805f9b34fb`
- Read characteristic: `00002b10-0000-1000-8000-00805f9b34fb` (Time Read)
- Write characteristic: `00002b11-0000-1000-8000-00805f9b34fb`
- Enable auto-upload command: `bytes([0x00, 0x01, 0x02, 0x0B, 0x01, 0x01])`
- Parse 30s pulse notifications into watts using configured `pulses_per_kwh`

### Naming Conventions
- Configuration keys use snake_case (e.g., `pulses_per_kwh`, `passkey`)
- Class names use PascalCase (e.g., `EmeraldBleClient`, `EmeraldConfigFlow`)
- Private methods/attributes use leading underscore (e.g., `_pulse_multiplier_kw`)
- Constants use UPPER_SNAKE_CASE (e.g., `SERVICE_UUID`, `DEFAULT_POLL_INTERVAL`)

## Development Workflow

### Syntax Validation
```bash
python -m compileall custom_components
```

### Configuration
- Default poll interval: 30 seconds
- Default pulses per kWh: 1000
- Update timeout: 8 seconds for BLE notification
- Connection retry using `bleak-retry-connector`

### Adding New Features
1. Update `const.py` if adding new constants or commands
2. Modify `coordinator.py` for new BLE commands or data parsing
3. Add entities in `sensor.py` (or new platforms like `binary_sensor.py`)
4. Update `strings.json` for UI text
5. Test syntax with `python -m compileall`

### Error Handling
- Use `UpdateFailed` exception in coordinator when BLE operations fail
- Log warnings for connection issues, timeouts
- Handle missing BLE device gracefully
- Provide meaningful error messages in config flow

## Common Tasks

### Adding a New Sensor
1. Parse new data in `EmeraldBleClient.async_fetch()`
2. Add sensor entity class in `sensor.py`
3. Register in `async_setup_entry()` in `sensor.py`
4. Add translations in `strings.json`

### Modifying BLE Protocol
1. Update UUIDs or commands in `const.py`
2. Adjust `async_fetch()` in `coordinator.py`
3. Update parsing logic for new packet formats
4. Test with actual hardware or BLE simulator

### Updating Config Flow
1. Modify schema in `config_flow.py`
2. Update `strings.json` for UI labels
3. Handle new configuration options in `coordinator.py`
4. Migrate existing entries if needed (bump `VERSION`)

## Resources

- **README.md:** Project overview and installation instructions
- **Home Assistant Docs:** https://developers.home-assistant.io/
- **BLE Protocol:** Documented in linked repository (see README references)
- **manifest.json:** Update `documentation` and `issue_tracker` URLs to match your deployment

## Notes

- This integration uses `local_polling` IoT class (no cloud dependency)
- Bluetooth must be enabled on the Home Assistant host
- Device must be within BLE range during setup and polling
- Passkey field is stored but not yet used for pairing (future enhancement)
