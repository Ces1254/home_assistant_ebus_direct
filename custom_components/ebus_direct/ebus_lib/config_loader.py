import logging
from pathlib import Path
import yaml

_LOGGER = logging.getLogger(__name__)

CONFIG_FILENAME = "ebus_entities.yaml"

def load_entities_config(user_path: Path) -> dict:
    """
    Load eBus sensor configuration.

    Priority:
    1. <base_path>/ebus_sensors.yaml
    2. integration default ebus_sensors.yaml (same folder as this file)
    """

    default_path = Path(__file__).parent.parent / CONFIG_FILENAME

    _LOGGER.debug("Declared user configfile path: %s", user_path)

    if user_path.exists():
        path_to_use = user_path
        _LOGGER.info("Loading user eBus sensor config: %s", user_path)
    else:
        path_to_use = default_path
        _LOGGER.info("Loading default eBus sensor config: %s", default_path)

    try:
        with open(path_to_use, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except Exception as err:
        _LOGGER.error("Failed to load eBus entities config: %s", err)
        return None, None, None
    
    sensors = data.get("sensors")

    if not isinstance(sensors, dict):
        _LOGGER.error("Invalid or missing 'sensors' section in %s", path_to_use)
        return None, None, None

    setpoints = data.get("setpoints")
    selects = data.get("selects")

    set_no = 0
    if setpoints: set_no = len(setpoints)
    if selects: set_no += len(selects)
    log_mex = f"Loaded {len(sensors)} eBus sensors"
    if setpoints or selects:
        log_mex = log_mex + f" and {set_no} eBus controls"
    else:
        log_mex = log_mex + ". No eBus controls loaded"
     
    _LOGGER.info(log_mex)
    return sensors, setpoints, selects
