#!/usr/bin/env python3

import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ebus_lib.ebusd import EbusdClient
from ebus_lib.get_param_value import get_val_by_tag, _LOGGER
from ebus_lib.config_loader import load_sensor_config


###############################################################################
# CONFIGURATION
###############################################################################

EBUSD_HOST = "192.168.31.111"   # chamge IP address as appropriate for your system
EBUSD_PORT = 8888
SCAN_INTERVAL = 20  # seconds

###############################################################################
# POLLING LOOP
###############################################################################

async def poll_loop(client: EbusdClient, sensors: dict):

    try:
        while True:
            data: dict[str, float] = {}

            for name, meta in sensors.items():
                
                value = await get_val_by_tag (client, meta)
                if value: 
                    unit = meta.get("unit",'') or ""
                    data[name] = value  + " " + unit
                else:
                    data[name] = "N/A"

            _LOGGER.info("=== POLL RESULT ===")
            for name, value in data.items():
                _LOGGER.info("  %-18s = %s", name, value)
            
            await asyncio.sleep(SCAN_INTERVAL)

    except asyncio.CancelledError:
        # Normal user end (^C in terminal)
        print("\n")
        raise


###############################################################################
# MAIN
###############################################################################

async def main():
    
    base_path = Path(".")
    sensors = load_sensor_config(base_path)

    if not sensors:
        sys.exit(1)
    
    client = EbusdClient(EBUSD_HOST, EBUSD_PORT)

    try:
        await client.connect()
        await poll_loop(client, sensors)
    
    except Exception as exc:
        _LOGGER.exception("Fatal error: %s", exc)

    finally:
        await client.close()

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)-7s %(message)s",)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("Interrupted by user")
        

