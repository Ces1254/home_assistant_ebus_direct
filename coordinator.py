from datetime import timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ebusd import EbusdClient
from .get_param_value import get_val_by_tag, _LOGGER

class EbusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client: EbusdClient, scan_interval: int, sensors):
        super().__init__(
            hass,
            _LOGGER,
            name="eBUS direct",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = client
        self._connected = False   # <- connection state
        self._sensors = sensors

    async def _ensure_connected(self):
        if self._client.is_connected:
            if not self._connected:
                _LOGGER.info("ebusd connection established")
                self._connected = True
            return

        try:
            await self._client.connect()
            _LOGGER.info("ebusd connected")
            self._connected = True

        except Exception as err:
            if self._connected:
                _LOGGER.warning("ebusd connection lost: %s", err)
            self._connected = False
            raise ConnectionError("ebusd connection failed") from err
   
    async def _async_update_data(self):
        try:
            await self._ensure_connected()

            data = {}
            for name, meta in self._sensors.items():
                value = await get_val_by_tag(self._client, meta)
                if value is not None:
                    data[name] = value
            return data

        except ConnectionError as err:
            await self._client.close()
            raise UpdateFailed("ebusd unavailable") from err

        except Exception as err:
            raise UpdateFailed(f"ebusd update failed: {err}") from err
