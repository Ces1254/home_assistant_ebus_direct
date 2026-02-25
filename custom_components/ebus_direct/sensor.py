from homeassistant.components.sensor import (
    SensorEntity,
    SensorStateClass,
    SensorDeviceClass,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

SENSOR_DEVICE_CLASS_MAP = {
    "temperature": SensorDeviceClass.TEMPERATURE,
    "power": SensorDeviceClass.POWER,
    "flow": SensorDeviceClass.VOLUME_FLOW_RATE,
    "frequency":  SensorDeviceClass.FREQUENCY,
}

async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[DOMAIN][entry.entry_id]
    sensors = data["sensors"]
    coordinator = data["coordinator"]
    device_info = data["device_info"]

    entities = [
        EbusSensor(
            coordinator,
            entry.entry_id,
            key,
            meta,
            device_info,
        )
        for key, meta in sensors.items()
    ]

    async_add_entities(entities)


class EbusSensor(CoordinatorEntity, SensorEntity):

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry_id, key, meta, device_info):
        super().__init__(coordinator)

        self._key = key

        # Entity name (suffix only, because has_entity_name = True)
        self._attr_name = meta["name"]

        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{key}"

        # Device association (single logical device)
        self._attr_device_info = device_info

        if meta.get("numeric", False):
            self._attr_native_unit_of_measurement = meta.get("unit")
            self._attr_device_class = SENSOR_DEVICE_CLASS_MAP.get(meta.get("device_class"),"")
            self._attr_state_class = SensorStateClass.MEASUREMENT
        else:
            # self._attr_entity_category = EntityCategory.DIAGNOSTIC
            self._attr_native_unit_of_measurement = None
            self._attr_device_class = None
            self._attr_state_class = None

    @property
    def native_value(self):
        value = self.coordinator.data.get(self._key)

        # Safety: ensure numeric sensors stay numeric
        if value is None:
            return None
        return value

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success

