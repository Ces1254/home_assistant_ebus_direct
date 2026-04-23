from homeassistant.components.switch import SwitchEntity

from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN
from .ebus_lib.get_param_value import get_val_by_tag, set_val_by_tag

async def async_setup_entry(hass, entry, async_add_entities):
 

    data = hass.data[DOMAIN][entry.entry_id]
    switches = data["switches"]
    if switches:
        client = data["client"]
        device_info = data["device_info"]

        entities = [
            EbusSwitch(client, entry.entry_id, key, meta, device_info)
            for key, meta in switches.items()
        ]

        async_add_entities(entities)


class EbusSwitch(SwitchEntity):

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, client, entry_id, key, meta, device_info):

        self._client = client
        self._meta = meta

        self._attr_name = meta["name"]
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{key}"
        self._attr_device_info = device_info

        self._value = None

    @property
    def is_on(self) -> bool:
        return str(self._value).lower() in ("on", "1", "true")

    async def async_added_to_hass(self):
        value = await get_val_by_tag(self._client, self._meta)
        self._value = value
        self.async_write_ha_state()

    async def async_update(self):
        value = await get_val_by_tag(self._client, self._meta)
        self._value = value

    async def async_turn_on(self, **kwargs):
        await set_val_by_tag(self._client, self._meta, "1")
        self._value = "On"
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await set_val_by_tag(self._client, self._meta, "0")
        self._value = "Off"
        self.async_write_ha_state() 
 