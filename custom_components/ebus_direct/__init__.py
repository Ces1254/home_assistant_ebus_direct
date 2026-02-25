"""Init file for ebus_direct integration - ebusd direct tcp link to HA."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity import DeviceInfo


from pathlib import Path

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL
from .const import CONF_DEVICE_NAME, CONF_DEVICE_MANUFACTURER, CONF_DEVICE_MODEL
from ebus_lib.ebusd import EbusdClient
from .coordinator import EbusCoordinator
from ebus_lib.config_loader import load_entities_config

PLATFORMS = ["sensor", "number", "select"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    scan_interval = entry.data[CONF_SCAN_INTERVAL]
    device_name = entry.data[CONF_DEVICE_NAME]
    device_manufacturer = entry.data[CONF_DEVICE_MANUFACTURER]
    device_model = entry.data[CONF_DEVICE_MODEL]

    config_path = Path(hass.config.path(DOMAIN))
    sensors, setpoints, selects = await hass.async_add_executor_job(load_entities_config, config_path)

    client = EbusdClient(host, port)
    await client.connect()

    coordinator = EbusCoordinator(hass, client, scan_interval, sensors)
    await coordinator.async_config_entry_first_refresh()

    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=device_name,
        manufacturer=device_manufacturer,
        model=device_model,
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "sensors": sensors,
        "setpoints": setpoints,
        "selects": selects,
        "client": client,
        "device_info":device_info,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def handle_reload(call: ServiceCall):
        await hass.config_entries.async_reload(entry.entry_id)

    hass.services.async_register(
        DOMAIN,
        "reload",
        handle_reload,
    )

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data:
            coordinator = data["coordinator"]
            await coordinator._client.close()

        # Remove reload service if no entries left
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "reload")

    return unload_ok