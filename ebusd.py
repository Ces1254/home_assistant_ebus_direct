import asyncio
import logging

_LOGGER = logging.getLogger(__name__)

class EbusdClient:
    def __init__(self, host: str, port: int):
        self._host = host
        self._port = port
        self._reader = None
        self._writer = None

    @property
    def is_connected(self) -> bool:
        return (
            self._writer is not None
            and not self._writer.is_closing()
        )

    async def connect(self):
        if self.is_connected:
            return

        _LOGGER.debug("Connecting to ebusd at %s:%s", self._host, self._port)

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=5,
            )
        except Exception as err:
            _LOGGER.warning(
                "Connection to ebusd failed (%s:%s): %s",
                self._host,
                self._port,
                err,
            )
            raise ConnectionError from err

    async def close(self):
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
            finally:
                self._writer = None
                self._reader = None

    async def clear_buffer(self):
        while not self._reader.at_eof():
            try:
                # read recursively until the buffer is empty
                # without waiting for more data to arrive.
                data = await asyncio.wait_for(self._reader.read(n=1024), timeout=0.01)
                if not data:
                    break
            except asyncio.TimeoutError:
                break
            
    async def command(self, cmd: str) -> str:
        if not self.is_connected:
            raise ConnectionError("Not connected to ebusd")
        
        try:
            await self.clear_buffer()
            self._writer.write((cmd + "\n").encode())
            await self._writer.drain()

            response = await asyncio.wait_for(
                self._reader.readline(),
                timeout=2
            )

            if not response:
                raise ConnectionResetError("EOF from ebusd")
            return response.decode(errors="ignore").strip()
            
        
        except (BrokenPipeError, ConnectionResetError, OSError) as err:
            await self.close()
            raise ConnectionError("ebusd connection lost") from err
        