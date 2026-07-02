from tuya2mqtt_local.profiles.plug import PlugProfile
from tuya2mqtt_local.profiles.dehumidifier_aircon import DehumidifierAirconProfile
from tuya2mqtt_local.profiles.kettle import KettleProfile
from tuya2mqtt_local.profiles.thermostat import ThermostatProfile

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

def test_thermostat_normalization_sets_hvac_mode():
    profile = ThermostatProfile()
    mappings = {
        "power": {"dps": "1"},
        "target_temperature": {"dps": "2", "scale": 2},
        "ambient_temperature": {"dps": "3", "scale": 2},
        "eco": {"dps": "5"},
        "child_lock": {"dps": "6"},
        "current_temperature": {"dps": "102", "scale": 2},
        "sensor_mode": {"dps": "103"},
        "thermostat_active": {"dps": "104"},
    }

    state = profile.normalize_state(
        {"1": True, "2": 50, "3": 39, "5": False, "6": True, "102": 38, "103": "1", "104": True},
        mappings,
    )

    assert state["power"] is True
    assert state["hvac_mode"] == "heat"
    assert state["target_temperature"] == 25
    assert state["ambient_temperature"] == 19.5
    assert state["eco"] is False
    assert state["child_lock"] is True
    assert state["current_temperature"] == 19
    assert state["sensor_mode"] == "1"
    assert state["thermostat_active"] is True

def test_thermostat_commands():
    profile = ThermostatProfile()
    mappings = {
        "power": {"dps": "1"},
        "target_temperature": {"dps": "2", "scale": 2},
        "eco": {"dps": "5"},
    }

    assert profile.command_to_dps("hvac_mode", "off", mappings) == [("1", False)]
    assert profile.command_to_dps("hvac_mode", "heat", mappings) == [("1", True)]
    assert profile.command_to_dps("target_temperature", "22.5", mappings) == [("2", 45)]
    assert profile.command_to_dps("eco", "ON", mappings) == [("5", True)]

def test_thermostat_discovery_includes_climate_without_mode_dps():
    profile = ThermostatProfile()
    components = profile.discovery_components(
        {
            "key": "bathroom-floor",
            "name": "Bathroom Floor",
            "mappings": {
                "power": {"dps": "1"},
                "target_temperature": {"dps": "2", "unit": "\u00b0C", "min": 5, "max": 35, "step": 0.5},
                "ambient_temperature": {"dps": "3", "scale": 2, "unit": "\u00b0C"},
                "eco": {"dps": "5"},
                "child_lock": {"dps": "6"},
                "current_temperature": {"dps": "102", "scale": 2, "unit": "\u00b0C"},
                "sensor_mode": {"dps": "103"},
                "thermostat_active": {"dps": "104"},
            },
        },
        {},
    )

    assert components["climate"]["p"] == "climate"
    assert components["climate"]["modes"] == ["off", "heat"]
    assert components["climate"]["mode_cmd_t"] == "~/set/hvac_mode"
    assert components["climate"]["curr_temp_tpl"] == "{{ value_json.current_temperature | float }}"
    assert components["eco"]["p"] == "switch"
    assert components["child_lock"]["p"] == "switch"
    assert "floor_temperature" not in components
    assert components["ambient_temperature"]["p"] == "sensor"
    assert components["sensor_mode"]["p"] == "sensor"
    assert components["thermostat_active"]["p"] == "binary_sensor"


def test_kettle_normalization():
    profile = KettleProfile()
    mappings = {
        "power": {"dps": "1"},
        "current_temperature": {"dps": "2", "unit": "\u00b0C"},
        "target_temperature": {"dps": "4", "unit": "\u00b0C"},
        "warm_time": {"dps": "7", "unit": "min"},
        "status": {"dps": "8"},
        "work_type": {"dps": "9"},
        "countdown": {"dps": "12", "unit": "min"},
        "countdown_left": {"dps": "13", "unit": "min"},
        "warm": {"dps": "14"},
    }

    state = profile.normalize_state(
        {
            "1": False,
            "2": 32,
            "4": 100,
            "7": 0,
            "8": "standby",
            "9": "heating_quick",
            "12": 0,
            "13": 0,
            "14": False,
        },
        mappings,
    )

    assert state == {
        "power": False,
        "current_temperature": 32,
        "target_temperature": 100,
        "warm_time": 0,
        "status": "standby",
        "work_type": "heating_quick",
        "countdown": 0,
        "countdown_left": 0,
        "warm": False,
    }


def test_kettle_commands():
    profile = KettleProfile()
    mappings = {
        "power": {"dps": "1"},
        "target_temperature": {"dps": "4"},
        "warm": {"dps": "14"},
        "work_type": {"dps": "9", "values": {"boiling_quick": "boiling_quick"}},
    }

    assert profile.command_to_dps("power", "ON", mappings) == [("1", True)]
    assert profile.command_to_dps("warm", "OFF", mappings) == [("14", False)]
    assert profile.command_to_dps("target_temperature", "90", mappings) == [("4", 90)]
    assert profile.command_to_dps("work_type", "boiling_quick", mappings) == [("9", "boiling_quick")]


def test_kettle_discovery_components():
    profile = KettleProfile()
    components = profile.discovery_components(
        {
            "key": "kettle",
            "name": "Kettle",
            "mappings": {
                "power": {"dps": "1"},
                "current_temperature": {"dps": "2", "unit": "\u00b0C"},
                "target_temperature": {"dps": "4", "unit": "\u00b0C", "min": 0, "max": 100, "step": 1},
                "status": {"dps": "8", "values": {"standby": "standby", "heating": "heating"}},
                "work_type": {"dps": "9", "values": {"boiling_quick": "boiling_quick"}},
                "warm": {"dps": "14"},
            },
        },
        {},
    )

    assert components["power"]["p"] == "switch"
    assert components["target_temperature"]["p"] == "number"
    assert components["target_temperature"]["cmd_t"] == "~/set/target_temperature"
    assert components["current_temperature"]["p"] == "sensor"
    assert components["current_temperature"]["dev_cla"] == "temperature"
    assert components["status"]["p"] == "sensor"
    assert components["work_type"]["p"] == "select"
    assert components["work_type"]["options"] == ["boiling_quick"]
    assert components["warm"]["p"] == "switch"
