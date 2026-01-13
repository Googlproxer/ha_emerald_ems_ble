from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="power_w",
        name="Power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
    ),
    SensorEntityDescription(
        key="pulses_30s",
        name="Pulses (30s)",
        device_class=None,
        native_unit_of_measurement=None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up sensors for a config entry."""

    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [EmeraldSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS]
    async_add_entities(entities)


class EmeraldSensor(CoordinatorEntity, SensorEntity):
    """Representation of an Emerald Energy Advisor measurement."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, description: SensorEntityDescription) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.client.address}_{description.key}"
        self._attr_name = description.name
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.client.address)},
            "name": coordinator.device_name,
            "manufacturer": "Emerald",
            "model": "Energy Advisor",
        }

    @property
    def native_value(self):
        return self.coordinator.data.get(self.entity_description.key)
