from homeassistant.components.select import (
    SelectEntity,
)

from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .ebus_lib.get_param_value import set_val_by_tag

async def async_setup_entry(hass, entry, async_add_entities):
 

    data = hass.data[DOMAIN][entry.entry_id]
    selects = data["selects"]
    if selects:
        device_info = data["device_info"]
        coordinator = data["coordinator"]

        entities = [
            EbusSelect(coordinator, entry.entry_id, key, meta, device_info)
            for key, meta in selects.items()
        ]

        async_add_entities(entities)


class EbusSelect(CoordinatorEntity, SelectEntity):

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator, entry_id, key, meta, device_info):
        super().__init__(coordinator)

        self._meta = meta
        self._key = key

        self._attr_name = meta["name"]
        self._attr_unique_id = f"{DOMAIN}_{entry_id}_{key}"
        self._attr_device_info = device_info
        self._attr_options = meta["options"]

    @property
    def current_option(self):
        return self.coordinator.data.get(self._key)
    
    @property
    def available(self):
        return self.coordinator.last_update_success


    async def async_select_option(self, option: str):

        read_back = await set_val_by_tag(self.coordinator._client, self._meta, option)

        if read_back is not None:
            self.coordinator.data[self._key] = read_back

        # Trigger refresh (important!)
        await self.coordinator.async_request_refresh()
    
