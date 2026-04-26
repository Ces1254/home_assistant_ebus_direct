from datetime import timedelta
import logging
import time
import asyncio

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .ebus_lib.ebusd import EbusdClient
from .ebus_lib.get_param_value import get_val_by_tag
from .const import SLOW_UPDATE_SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

SLOW_INTERVAL = 14400

class EbusCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, client: EbusdClient, scan_interval: int, sensors, slow_upd_entities = None):
        super().__init__(
            hass,
            _LOGGER,
            name="eBUS direct",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = client
        self._connected = False   # <- connection state
        self._sensors = sensors
        self._slow_upd_entities = slow_upd_entities or {}
        self._last_slow_update = 0

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

            data = dict(self.data or {})
            for name, meta in self._sensors.items():
                value = await get_val_by_tag(self._client, meta)
                if value is not None:
                    data[name] = value

            now = time.monotonic()

            if self._slow_upd_entities and now - self._last_slow_update > SLOW_UPDATE_SCAN_INTERVAL:

                for name, meta in self._slow_upd_entities.items():
                    value = await asyncio.wait_for(
                        get_val_by_tag(self._client, meta),
                        timeout=5
                    )
                    if value is not None:
                        data[name] = value

                self._last_slow_update = now

            return data

        except ConnectionError as err:
            await self._client.close()
            raise UpdateFailed("ebusd unavailable") from err

        except Exception as err:
            raise UpdateFailed(f"ebusd update failed: {err}") from err

    async def shutdown(self):
        await self._client.close()
        self._connected = False