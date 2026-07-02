import logging
import json
from typing import Any

def redact_config(config: dict[str, Any]) -> dict[str, Any]:
    """Redact sensitive information from config for logging."""
    redacted = json.loads(json.dumps(config))
    if "devices" in redacted:
        for device in redacted["devices"]:
            if "local_key" in device:
                device["local_key"] = "****"
    if "mqtt" in redacted:
        if "password" in redacted["mqtt"] and redacted["mqtt"]["password"]:
            redacted["mqtt"]["password"] = "****"
    return redacted

def setup_logging(level: str = "INFO"):
    """Setup basic logging."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

def parse_raw_value(value: str) -> Any:
    """Parse raw string value from MQTT to appropriate Python type."""
    # Try JSON parsing first
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        pass

    # Fallback string parsing
    val_upper = value.upper()
    if val_upper in ("ON", "TRUE"):
        return True
    if val_upper in ("OFF", "FALSE"):
        return False
    
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value