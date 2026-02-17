import logging
from pathlib import Path
import yaml

_LOGGER = logging.getLogger(__name__)

CONFIG_FILENAME = "ebus_sensors.yaml"


def load_sensor_config(base_path: Path) -> dict:
    """
    Load eBus sensor configuration.

    Priority:
    1. <base_path>/ebus_sensors.yaml
    2. integration default ebus_sensors.yaml (same folder as this file)
    """

    user_path = base_path / CONFIG_FILENAME
    default_path = Path(__file__).parent.parent / "custom_components/ebus_direct/" / CONFIG_FILENAME

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
        _LOGGER.error("Failed to load eBus sensor config: %s", err)
        return {}

    sensors = data.get("sensors")

    if not isinstance(sensors, dict):
        _LOGGER.error("Invalid or missing 'sensors' section in %s", path_to_use)
        return {}

    _LOGGER.info("Loaded %d eBus sensors", len(sensors))
    return sensors
