"""Init file for ebus_direct integration - ebusd direct tcp link to HA."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.entity import DeviceInfo

import logging
from pathlib import Path

from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
from .const import CONF_DEVICE_NAME, CONF_DEVICE_MANUFACTURER, CONF_DEVICE_MODEL
from .ebus_lib.ebusd import EbusdClient
from .coordinator import EbusCoordinator
from .ebus_lib.config_loader import load_entities_config

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config):
    conf = config.get(DOMAIN)
    if not conf:
        _LOGGER.error("Entities file not defined in configuration.yaml: please update it.")
        return False  # not configured

    entities_file = conf.get("entities_file", "ebus_entities.yaml")

    file_path = Path(hass.config.path(entities_file))

    if not file_path.exists():
        _LOGGER.error("Entities file not found: %s", file_path)
        _LOGGER.info("Create the file %s and reload the integration", entities_file)
        return False

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["entities_file"] = file_path

    async def handle_reload(call: ServiceCall):
        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)

    if not hass.services.has_service(DOMAIN, "reload"):
        hass.services.async_register(
            DOMAIN,
            "reload",
            handle_reload,
        )

    return True

PLATFORMS = ["sensor", "number", "select"]

async def async_reload_entry(hass, entry):
    await hass.config_entries.async_reload(entry.entry_id)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
#    scan_interval = entry.data[CONF_SCAN_INTERVAL]
    scan_interval = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )

    device_name = entry.data[CONF_DEVICE_NAME]
    device_manufacturer = entry.data[CONF_DEVICE_MANUFACTURER]
    device_model = entry.data[CONF_DEVICE_MODEL]

    hass.data.setdefault(DOMAIN, {})
    
    user_defined_path = hass.data[DOMAIN].get("entities_file")
    if not user_defined_path:
        _LOGGER.error("Entities file not defined in configuration.yaml: please update it.")
        return False

    sensors, setpoints, selects = await hass.async_add_executor_job(load_entities_config, user_defined_path)

    entry.async_on_unload(
        entry.add_update_listener(async_reload_entry)
    )
    
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

    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "sensors": sensors,
        "setpoints": setpoints,
        "selects": selects,
        "client": client,
        "device_info":device_info,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        data = hass.data[DOMAIN].pop(entry.entry_id, None)
        if data:
            coordinator = data["coordinator"]
            await coordinator.shutdown()            

        # Remove reload service if no entries left
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "reload")

    return unload_ok

