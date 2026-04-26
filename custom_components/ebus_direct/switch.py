from homeassistant.components.switch import SwitchEntity

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .ebus_lib.get_param_value import set_val_by_tag

async def async_setup_entry(hass, entry, async_add_entities):
 

    data = hass.data[DOMAIN][entry.entry_id]
    switches = data["switches"]
    if switches:
        device_info = data["device_info"]
        coordinator = data["coordinator"]


        entities = [
            EbusSwitch(coordinator, entry.entry_id, key, meta, device_info)
            for key, meta in switches.items()
        ]

        async_add_entities(entities)


class EbusSwitch(CoordinatorEntity, SwitchEntity):

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator, entry_id, key, meta, device_info):
        super().__init__(coordinator)

        self._key = key
        self._meta = meta
        
        self._attr_name = meta["name"]
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{key}"
        self._attr_device_info = device_info


    @property
    def is_on(self) -> bool:
        return str(self.coordinator.data[self._key]).lower() in ("on", "1", "true")
    
    @property
    def available(self):
        return self.coordinator.last_update_success
    

    async def async_turn_on(self, **kwargs):
        await set_val_by_tag(self.coordinator._client, self._meta, "1")
        self.coordinator.data[self._key] = "On"
        await self.coordinator.async_request_refresh()
       

    async def async_turn_off(self, **kwargs):
        await set_val_by_tag(self.coordinator._client, self._meta, "0")
        self.coordinator.data[self._key] = "Off"
        await self.coordinator.async_request_refresh()
 