#!/usr/bin/env python3

import sys
import asyncio
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ebus_lib.ebusd import EbusdClient
from ebus_lib.get_param_value import get_val_by_tag, set_val_by_tag, _LOGGER
from ebus_lib.config_loader import load_entities_config


###############################################################################
# CONFIGURATION
###############################################################################

EBUSD_HOST = "192.168.31.111"   # chamge IP address as appropriate for your system
EBUSD_PORT = 8888
SCAN_INTERVAL = 20  # seconds

import select

###############################################################################
# KEYBOARD HELPER
###############################################################################

async def wait_for_keypress():
    """Return when any key is pressed."""
    loop = asyncio.get_running_loop()

    def _check():
        r, _, _ = select.select([sys.stdin], [], [], 0)
        return bool(r)

    while True:
        if await loop.run_in_executor(None, _check):
            sys.stdin.readline()
            return
        await asyncio.sleep(0.1)

###############################################################################
# POLLING LOOP
###############################################################################

async def poll_loop(client: EbusdClient, sensors: dict):

    print("Polling started — press 'Enter' to stop")
    print(" ")

    stop_task = asyncio.create_task(wait_for_keypress())

    try:
        while not stop_task.done():

            data: dict[str, float] = {}

            for name, meta in sensors.items():
                value = await get_val_by_tag(client, meta)
                unit = meta.get("unit", "") or ""
                data[name] = f"{value} {unit}" if value is not None else "N/A"

            _LOGGER.info("=== POLL RESULT ===")
            for name, value in data.items():
                _LOGGER.info("  %-18s = %s", name, value)

            for _ in range(SCAN_INTERVAL):
                if stop_task.done(): break
                await asyncio.sleep(1.)

    finally:
        stop_task.cancel()
        print("\nPolling stopped.\n")

###############################################################################
# EDIT SETPOINT VALUES
###############################################################################

async def adjust_setpoints(client, setpoints, selects):

    while True:

        print("\n=== Setpoints and selections ===")

        items = list(setpoints.items()) + list(selects.items())

        for i, (key, meta) in enumerate(items, 1):
            val = await get_val_by_tag(client, meta)
            unit = meta.get("unit", "") or ""
            if unit is not "": unit = f" {unit}" 
            print(f"{i} - {meta['name']} ({val}{unit})")

        print("0 - back")

        choice = await asyncio.to_thread(input, "select > ")

        if choice == "0":
            return

        try:
            idx = int(choice) - 1
            key, meta = items[idx]
        except (ValueError, IndexError):
            print("Invalid selection")
            continue

        current = await get_val_by_tag(client, meta)
        print(f"Current value: {current}")

        opts = meta.get("options")

        if not opts:
            new_val = await asyncio.to_thread(input, "Enter new value: ")

            try:
                new_val = float(new_val)
            except ValueError:
                print("Invalid number")
                continue

            step = meta.get("step",0)
            current = float(current)
            if abs(new_val - current) <= step:
                print("nothing to update")
                continue
        else:
            for i, opt in enumerate(opts, 1):
                print(f"{i} - {opt}")

            print("0 - back")

            choice = await asyncio.to_thread(input, "select > ")

            if choice == "0":
                return
            
            idx = int(choice) - 1
            new_val = opts[idx]
            if new_val in current: 
                print("nothing to update")
                continue

        read_back = await set_val_by_tag(client, meta, new_val)

        print(f"New value confirmed: {read_back}")

###############################################################################
# Get USER INPUT
###############################################################################

async def interactive_console(client, sensors, setpoints, selects):

    while True:

        print("\n=== MAIN MENU ===")
        print("1 - start sensors poll")
        print("2 - adjust setpoints and selections")
        print("q - quit")

        choice = await asyncio.to_thread(input, "select > ")

        if choice == "1":
            await poll_loop(client, sensors)

        elif choice == "2":
            await adjust_setpoints(client, setpoints, selects)

        elif choice.lower() == "q":
            return

        else:
            print("Invalid selection")

###############################################################################
# MAIN
###############################################################################

async def main():
    
    base_path = Path(".")
    sensors, setpoints, selects = load_entities_config(base_path)

    if not sensors:
        sys.exit(1)
    
    client = EbusdClient(EBUSD_HOST, EBUSD_PORT)

    try:
        await client.connect()
        await interactive_console(client, sensors, setpoints, selects)

    except Exception as exc:
        _LOGGER.exception("Fatal error: %s", exc)

    finally:
        await client.close()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-7s %(message)s",)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        _LOGGER.info("Interrupted by user")
        

