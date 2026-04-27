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
        return None, None, None, None
    
    data = check_entities_config (data)
 
    sensors = data.get("sensors")

    if not isinstance(sensors, dict):
        _LOGGER.error("Invalid or missing 'sensors' section in %s", path_to_use)
        return None, None, None, None

    setpoints = data.get("setpoints")
    selects = data.get("selects")
    switches = data.get("switches")
 
    set_no = 0
    if setpoints: set_no = len(setpoints)
    if selects: set_no += len(selects)
    if switches: set_no += len(switches)
    log_mex = f"Loaded {len(sensors)} eBus sensors"
    if setpoints or selects or switches:
        log_mex = log_mex + f" and {set_no} eBus controls"
    else:
        log_mex = log_mex + ". No eBus controls loaded"
     
    _LOGGER.info(log_mex)
    return sensors, setpoints, selects, switches

def check_entities_config(entities_data):
    """
    Validate and clean eBus entities configuration.
    Returns a new sanitized dict.
    """

    def validate_sensor(key, meta):
        if meta.get("name", "") == "":
            _LOGGER.error("Missing 'name' for sensor %s", key)
            return False

        if (
            meta.get("ebus_find_tag", "") == "" and
            meta.get("ebus_read_tag", "") == "" and
            meta.get("ebus_rw_tag", "") == ""
        ):
            _LOGGER.error("Missing find/read 'tag' for sensor %s", key)
            return False

        return True

    def validate_setpoint(key, meta):
        if meta.get("name", "") == "":
            _LOGGER.error("Missing 'name' for setpoint %s", key)
            return False

        if meta.get("ebus_rw_tag", "") == "":
            _LOGGER.error("Missing write 'tag' for setpoint %s", key)
            return False

        return True

    def validate_select(key, meta):
        if meta.get("name", "") == "":
            _LOGGER.error("Missing 'name' for select %s", key)
            return False

        if meta.get("ebus_rw_tag", "") == "":
            _LOGGER.error("Missing write 'tag' for select %s", key)
            return False

        if not meta.get("options"):
            _LOGGER.error("Missing 'options' for select %s", key)
            return False

        return True

    def validate_switch(key, meta):
        if meta.get("name", "") == "":
            _LOGGER.error("Missing 'name' for switch %s", key)
            return False

        if meta.get("ebus_rw_tag", "") == "":
            _LOGGER.error("Missing write 'tag' for switch %s", key)
            return False

        return True

    # ---- rebuild sections ----

    validated = {}

    sensors = entities_data.get("sensors")
    if isinstance(sensors, dict):
        validated["sensors"] = {
            key: meta for key, meta in sensors.items()
            if validate_sensor(key, meta)
        }

    setpoints = entities_data.get("setpoints")
    if isinstance(setpoints, dict):
        validated["setpoints"] = {
            key: meta for key, meta in setpoints.items()
            if validate_setpoint(key, meta)
        }

    selects = entities_data.get("selects")
    if isinstance(selects, dict):
        validated["selects"] = {
            key: meta for key, meta in selects.items()
            if validate_select(key, meta)
        }

    switches = entities_data.get("switches")
    if isinstance(switches, dict):
        validated["switches"] = {
            key: meta for key, meta in switches.items()
            if validate_switch(key, meta)
        }

    return validated