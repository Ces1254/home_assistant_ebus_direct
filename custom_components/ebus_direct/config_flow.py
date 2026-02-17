from homeassistant import config_entries
import voluptuous as vol
from ebus_lib.ebusd import EbusdClient

from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    CONF_DEVICE_NAME,
    CONF_DEVICE_MANUFACTURER,
    CONF_DEVICE_MODEL,
    DEFAULT_DEVICE_NAME,
    DEFAULT_DEVICE_MANUFACTURER,
    DEFAULT_DEVICE_MODEL,
)

class EbusDirectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}

        if user_input is not None:
            try:
                client = EbusdClient(
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                )
                await client.connect()
                await client.close()

            except Exception:
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"eBUS direct TCP link via ebusd({user_input[CONF_HOST]})",
                    data=user_input,
                )

        schema = vol.Schema({
            vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): int,
            vol.Optional(CONF_DEVICE_NAME, default=DEFAULT_DEVICE_NAME): str,
            vol.Optional(CONF_DEVICE_MANUFACTURER, default=DEFAULT_DEVICE_MANUFACTURER): str,
            vol.Optional(CONF_DEVICE_MODEL, default=DEFAULT_DEVICE_MODEL): str,
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
