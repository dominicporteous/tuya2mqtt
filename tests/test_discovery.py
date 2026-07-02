import pytest
from tuya2mqtt_local.discovery import get_discovery_payload

def test_discovery_payload_plug():
    device_config = {
        "key": "office-plug",
        "name": "Office Plug",
        "id": "bf1234567890abcdef",
        "ip": "192.168.0.55",
        "local_key": "abcdef0123456789",
        "profile": "plug",
        "manufacturer": "Tuya",
        "model": "Generic Power Plug",
        "product_name": "Tuya Smart Socket",
        "mappings": {
            "switch": {"dps": "1"},
            "power": {"dps": "19", "unit": "W"}
        }
    }
    mqtt_config = {
        "base_topic": "tuya",
        "discovery_prefix": "homeassistant"
    }
    
    payload = get_discovery_payload(device_config, mqtt_config)
    
    assert payload["dev"]["ids"] == ["tuya_bf1234567890abcdef"]
    assert payload["dev"]["name"] == "Office Plug"
    assert payload["dev"]["mdl"] == "Tuya Smart Socket"
    assert payload["state_topic"] == "tuya/office-plug/state"
    assert "switch" in payload["cmps"]
    assert "power" in payload["cmps"]
    assert payload["cmps"]["switch"]["p"] == "switch"
    assert payload["cmps"]["power"]["p"] == "sensor"


def test_discovery_payload_model_falls_back_to_config_model():
    device_config = {
        "key": "office-plug",
        "name": "Office Plug",
        "id": "bf1234567890abcdef",
        "ip": "192.168.0.55",
        "local_key": "abcdef0123456789",
        "profile": "plug",
        "model": "Generic Power Plug",
        "mappings": {
            "switch": {"dps": "1"},
        },
    }
    mqtt_config = {
        "base_topic": "tuya",
        "discovery_prefix": "homeassistant",
    }

    payload = get_discovery_payload(device_config, mqtt_config)

    assert payload["dev"]["mdl"] == "Generic Power Plug"
