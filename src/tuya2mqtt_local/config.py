import yaml
import os
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Mapping from Tuya category to internal profile name
CATEGORY_TO_PROFILE = {
    "bh": "kettle",  # Kettle
    "cz": "plug",  # Socket/Plug
    "kt": "dehumidifier_aircon",  # Air Conditioner
    "wk": "thermostat",  # Thermostat
}

# Mapping from Tuya DP codes to internal mapping keys
DP_CODE_TO_INTERNAL = {
    "switch": "power",
    "cur_current": "current",
    "cur_power": "power",
    "cur_voltage": "voltage",
    "countdown_1": "countdown",
    "countdown": "countdown",
    "countdown_left": "countdown_left",
    "start": "power",
    "temp_set": "target_temperature",
    "temp_current": "current_temperature",
    "mode": "mode",
    "status": "status",
    "warm": "warm",
    "warm_time": "warm_time",
    "work_type": "work_type",
    "fan_speed_enum": "fan_mode",
    "humidity_set": "target_humidity",
    "humidity_current": "current_humidity",
    "child_lock": "child_lock",
    "eco": "eco",
    "upper_temp": "ambient_temperature",
}

# Translation for common Tuya values to Home Assistant standard values
VALUE_TRANSLATIONS = {
    "mode": {"cold": "cool", "hot": "heat", "wet": "dry", "wind": "fan_only", "auto": "auto"}
}

THERMOSTAT_LOCAL_FALLBACK_MAPPINGS = {
    # Some WT81-family thermostats report these DPS locally even though they are
    # omitted from the Tuya cloud schema returned in devices.json.
    "current_temperature": {"dps": "102", "type": "integer", "scale": 2, "unit": "\u00b0C"},
    "sensor_mode": {"dps": "103", "type": "string"},
    "thermostat_active": {"dps": "104", "type": "boolean"},
}


def load_config(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config file not found: {path}")
    
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    # Try to load supplemental info from devices.json
    config_dir = os.path.dirname(os.path.abspath(path))
    devices_json_path = os.path.join(config_dir, "devices.json")
    
    devices_json = []
    if os.path.exists(devices_json_path):
        try:
            with open(devices_json_path, "r") as f:
                devices_json = json.load(f)
            logger.info(f"Loaded supplemental device info from {devices_json_path}")
        except Exception as e:
            logger.warning(f"Failed to load {devices_json_path}: {e}")

    # Merge supplemental info
    if "devices" in config and isinstance(config["devices"], list):
        for device in config["devices"]:
            device_id = device.get("id")
            if not device_id:
                continue

            # Find matching device in devices.json
            match = next((d for d in devices_json if d.get("id") == device_id), None)
            if match:
                # Merge missing fields
                if "local_key" not in device and "key" in match:
                    device["local_key"] = match["key"]
                if "name" not in device and "name" in match:
                    device["name"] = match["name"]
                if "version" not in device and "version" in match:
                    device["version"] = str(match["version"])
                if "product_name" not in device:
                    product_name = _device_product_name(match)
                    if product_name:
                        device["product_name"] = product_name
                if "profile" not in device:
                    category = match.get("category")
                    if category in CATEGORY_TO_PROFILE:
                        device["profile"] = CATEGORY_TO_PROFILE[category]
                        logger.debug(f"Auto-mapped device {device_id} (category {category}) to profile {device['profile']}")
                else:
                    category = match.get("category")
                    expected_profile = CATEGORY_TO_PROFILE.get(category)
                    if expected_profile and device["profile"] != expected_profile:
                        logger.warning(
                            "Device %s has profile=%s in config.yaml, but devices.json category %s maps to profile=%s",
                            device_id,
                            device["profile"],
                            category,
                            expected_profile,
                        )

                # Populate mappings from devices.json if missing in config.yaml
                if "mappings" not in device and "mapping" in match:
                    device["mappings"] = {}
                    for dps_id, info in match["mapping"].items():
                        code = info.get("code")
                        type = info.get("type")
                        if code in DP_CODE_TO_INTERNAL:
                            internal_key = _internal_mapping_key(device.get("profile"), code)
                            m = {"dps": str(dps_id), "type": type.lower()}
                            
                            # Handle scale (Tuya scale 1 = divide by 10)
                            # But TinyTuya wizard output format varies. 
                            # If scale is 1, it usually means 1 decimal place.
                            values = info.get("values", {})
                            if isinstance(values, dict):
                                scale = values.get("scale")
                                scale_divisor = 10 ** scale if isinstance(scale, int) and scale > 0 else None
                                if scale_divisor:
                                    m["scale"] = scale_divisor
                                if "min" in values:
                                    m["min"] = _scale_mapping_bound(values["min"], scale_divisor)
                                if "max" in values:
                                    m["max"] = _scale_mapping_bound(values["max"], scale_divisor)
                                if "step" in values:
                                    m["step"] = _scale_mapping_bound(values["step"], scale_divisor)
                                if "unit" in values:
                                    m["unit"] = values["unit"]
                                
                                # Mode/Fan translation
                                if code == "mode" and "range" in values:
                                    translations = VALUE_TRANSLATIONS.get("mode", {})
                                    m["values"] = {v: translations.get(v, v) for v in values["range"]}
                                if code == "fan_speed_enum" and "range" in values:
                                    m["values"] = {v: v for v in values["range"]}
                                if (
                                    device.get("profile") == "kettle"
                                    and code in ("status", "work_type")
                                    and "range" in values
                                ):
                                    m["values"] = {v: v for v in values["range"]}

                            if device.get("profile") == "thermostat" and code in ("temp_set", "upper_temp"):
                                m["scale"] = 2
                                if "min" in values:
                                    m["min"] = values["min"] / 2
                                if "max" in values:
                                    m["max"] = values["max"] / 2
                                if code == "temp_set":
                                    m["step"] = 0.5
                                elif "step" in values:
                                    m["step"] = values["step"]

                            device["mappings"][internal_key] = m

                    if device.get("profile") == "thermostat":
                        for key, mapping in THERMOSTAT_LOCAL_FALLBACK_MAPPINGS.items():
                            device["mappings"].setdefault(key, mapping.copy())
                    
                    logger.debug(f"Auto-generated mappings for {device_id}: {list(device['mappings'].keys())}")

    validate_config(config)
    return config

def _internal_mapping_key(profile: str | None, code: str) -> str:
    if profile == "plug" and code == "switch":
        return "switch"
    return DP_CODE_TO_INTERNAL[code]

def _scale_mapping_bound(value: Any, scale: int | None) -> Any:
    if scale and isinstance(value, (int, float)):
        return value / scale
    return value

def _device_product_name(device: dict[str, Any]) -> str | None:
    for key in ("product_name", "productName", "product name"):
        value = device.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return None

def validate_config(config: dict[str, Any]):
    required_sections = ["mqtt", "bridge", "devices"]
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section in config: {section}")
            
    mqtt = config["mqtt"]
    required_mqtt = ["host"]
    for field in required_mqtt:
        if field not in mqtt:
            raise ValueError(f"Missing required MQTT field: {field}")
            
    bridge = config.get("bridge", {})
    if "exit_on_command_error" not in bridge:
        bridge["exit_on_command_error"] = True
    config["bridge"] = bridge

    devices = config["devices"]
    if not isinstance(devices, list):
        raise ValueError("Devices section must be a list")
        
    required_device = ["id", "ip", "name", "local_key", "profile"]
    for device in devices:
        # Ensure 'key' is present as it's used internally as a handle for MQTT topics
        if "key" not in device:
            device["key"] = device.get("id")

        for field in required_device:
            if field not in device:
                # Use ID or key for error reporting
                identifier = device.get("id") or device.get("key") or "unknown"
                raise ValueError(f"Device {identifier} is missing required field: {field} (and it wasn't found in devices.json)")
