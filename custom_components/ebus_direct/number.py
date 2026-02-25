
from homeassistant.components.number import (
    NumberEntity,    
    NumberDeviceClass,
)

from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from ebus_lib.get_param_value import get_val_by_tag, set_val_by_tag, _LOGGER

NUMBER_DEVICE_CLASS_MAP = {
    "temperature": NumberDeviceClass.TEMPERATURE,
}


async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[DOMAIN][entry.entry_id]
    setpoints = data["setpoints"]
    client = data["client"]

    device_info = DeviceInfo(
        identifiers={(DOMAIN, "wolf")},
        name="Heat Pump",
        manufacturer="Wolf",
        model="FHA via eBus",
    )

    entities = [
        WolfEbusSetpoint(client, entry.entry_id, key, meta, device_info)
        for key, meta in setpoints.items()
    ]

    async_add_entities(entities)

class WolfEbusSetpoint(NumberEntity):

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, client, entry_id, key, meta, device_info):
        self._client = client
        self._meta = meta

        # Entity name (suffix only, because has_entity_name = True)
        self._attr_name = meta["name"]

        # Stable Home Assistant unique ID
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{key}"

        # Device association (single logical device)
        self._attr_device_info = device_info

        self._attr_native_unit_of_measurement = meta.get("unit")
        self._attr_device_class = NUMBER_DEVICE_CLASS_MAP.get(meta.get("device_class"))
        self._attr_native_min_value = meta.get("min")
        self._attr_native_max_value = meta.get("max")
        self._attr_native_step = meta.get("step", 0.5)

        self._value = None


    @property
    def native_value(self):
        return self._value
    
    async def async_added_to_hass(self):
        """Called when entity is added to HA."""
        await self.async_update()

    async def async_set_native_value(self, value):
        """User changed the setpoint."""
    
        read_back = await set_val_by_tag(self._client, self._meta, value)
        
        try:
            self._value = float(read_back)
        except:
            _LOGGER.warning("Failed to update setpoint")
            self._value = None

        self.async_write_ha_state()

    async def async_update(self):
        value = await get_val_by_tag(self._client, self._meta)        
        if value is not None:
            self._value = float(value)
        self.async_write_ha_state()


