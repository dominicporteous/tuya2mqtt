import pytest
from tuya2mqtt_local.profiles.plug import PlugProfile
from tuya2mqtt_local.profiles.dehumidifier_aircon import DehumidifierAirconProfile

def test_plug_normalization():
    profile = PlugProfile()
    mappings = {
        "switch": {"dps": "1"},
        "power": {"dps": "19", "scale": 10},
        "voltage": {"dps": "20", "scale": 10},
        "current": {"dps": "18", "scale": 1000},
        "countdown": {"dps": "2", "unit": "s"},
    }
    raw_dps = {"1": True, "19": 126, "20": 2354, "18": 31, "2": 300}
    
    state = profile.normalize_state(raw_dps, mappings)
    assert state["power"] is True
    assert state["power_w"] == 12.6
    assert state["voltage_v"] == 235.4
    assert state["current_a"] == 0.031
    assert state["countdown_s"] == 300

def test_plug_discovery_includes_countdown_sensor():
    profile = PlugProfile()
    components = profile.discovery_components(
        {
            "key": "office-plug",
            "name": "Office Plug",
            "mappings": {
                "countdown": {"dps": "2", "unit": "s"},
            },
        },
        {},
    )

    assert components["countdown"]["p"] == "sensor"
    assert components["countdown"]["dev_cla"] == "duration"
    assert components["countdown"]["unit_of_meas"] == "s"
    assert components["countdown"]["val_tpl"] == "{{ value_json.countdown_s }}"

def test_plug_command():
    profile = PlugProfile()
    mappings = {"switch": {"dps": "1"}}
    
    [(dps, val)] = profile.command_to_dps("switch", "ON", mappings)
    assert dps == "1"
    assert val is True
    
    [(dps, val)] = profile.command_to_dps("switch", "OFF", mappings)
    assert dps == "1"
    assert val is False

def test_aircon_mode_mapping():
    profile = DehumidifierAirconProfile()
    mappings = {
        "mode": {
            "dps": "2",
            "values": {
                "wet": "dry",
                "cold": "cool"
            }
        }
    }
    
    # Normalization
    state = profile.normalize_state({"2": "wet"}, mappings)
    assert state["mode"] == "dry"
    
    # Command reverse mapping
    [(dps, val)] = profile.command_to_dps("mode", "dry", mappings)
    assert dps == "2"
    assert val == "wet"

def test_aircon_temp_scaling():
    profile = DehumidifierAirconProfile()
    mappings = {
        "target_temperature": {"dps": "3"}
    }
    
    [(dps, val)] = profile.command_to_dps("target_temperature", "22", mappings)
    assert dps == "3"
    assert val == 22
