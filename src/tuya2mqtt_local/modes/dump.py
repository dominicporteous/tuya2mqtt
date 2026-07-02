import json
import logging
from typing import Any
from ..tuya import TuyaClient

logger = logging.getLogger(__name__)

def dump_mode(config: dict[str, Any], device_key: str):
    """One-shot raw status dump."""
    device_config = next((d for d in config["devices"] if d["key"] == device_key), None)
    if not device_config:
        print(json.dumps({"error": f"Device {device_key} not found in config"}))
        return

    client = TuyaClient(device_config)
    dps = client.status()
    
    output = {
        "device": device_key,
        "id": device_config["id"],
        "ip": device_config["ip"],
        "version": device_config.get("version", "3.3"),
        "dps": dps if dps else {}
    }
    
    print(json.dumps(output, indent=2))