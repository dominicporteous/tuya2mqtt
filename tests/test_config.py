import json

import yaml

from tuya2mqtt_local.config import load_config


def test_plug_auto_mapping_uses_switch_key(tmp_path):
    config_path = tmp_path / "config.yaml"
    devices_path = tmp_path / "devices.json"

    config_path.write_text(
        yaml.safe_dump(
            {
                "mqtt": {"host": "localhost"},
                "bridge": {},
                "devices": [{"id": "plug-device", "ip": "192.168.1.50"}],
            }
        )
    )
    devices_path.write_text(
        json.dumps(
            [
                {
                    "id": "plug-device",
                    "name": "Office Plug",
                    "key": "0123456789abcdef",
                    "product_name": "Tuya Smart Socket",
                    "category": "cz",
                    "mapping": {
                        "1": {
                            "code": "switch",
                            "type": "Boolean",
                            "values": {},
                        },
                        "2": {
                            "code": "countdown_1",
                            "type": "Integer",
                            "values": {"unit": "s", "min": 0, "max": 86400, "scale": 0, "step": 1},
                        },
                        "4": {
                            "code": "cur_current",
                            "type": "Integer",
                            "values": {"unit": "mA", "min": 0, "max": 30000, "scale": 0, "step": 1},
                        },
                        "5": {
                            "code": "cur_power",
                            "type": "Integer",
                            "values": {"unit": "W", "min": 0, "max": 50000, "scale": 0, "step": 1},
                        },
                        "6": {
                            "code": "cur_voltage",
                            "type": "Integer",
                            "values": {"unit": "V", "min": 0, "max": 2500, "scale": 0, "step": 1},
                        }
                    },
                }
            ]
        )
    )

    config = load_config(str(config_path))

    [device] = config["devices"]
    assert device["profile"] == "plug"
    assert device["product_name"] == "Tuya Smart Socket"
    assert device["mappings"] == {
        "switch": {"dps": "1", "type": "boolean"},
        "countdown": {"dps": "2", "type": "integer", "min": 0, "max": 86400, "step": 1, "unit": "s"},
        "current": {"dps": "4", "type": "integer", "min": 0, "max": 30000, "step": 1, "unit": "mA"},
        "power": {"dps": "5", "type": "integer", "min": 0, "max": 50000, "step": 1, "unit": "W"},
        "voltage": {"dps": "6", "type": "integer", "min": 0, "max": 2500, "step": 1, "unit": "V"},
    }


def test_devices_json_product_name_variants_are_normalized(tmp_path):
    config_path = tmp_path / "config.yaml"
    devices_path = tmp_path / "devices.json"

    config_path.write_text(
        yaml.safe_dump(
            {
                "mqtt": {"host": "localhost"},
                "bridge": {},
                "devices": [{"id": "plug-device", "ip": "192.168.1.50"}],
            }
        )
    )
    devices_path.write_text(
        json.dumps(
            [
                {
                    "id": "plug-device",
                    "name": "Office Plug",
                    "key": "0123456789abcdef",
                    "productName": "Camel Case Socket",
                    "category": "cz",
                }
            ]
        )
    )

    config = load_config(str(config_path))

    [device] = config["devices"]
    assert device["product_name"] == "Camel Case Socket"


def test_thermostat_auto_mapping_uses_wk_category(tmp_path):
    config_path = tmp_path / "config.yaml"
    devices_path = tmp_path / "devices.json"

    config_path.write_text(
        yaml.safe_dump(
            {
                "mqtt": {"host": "localhost"},
                "bridge": {},
                "devices": [{"id": "thermostat-device", "ip": "192.168.1.51"}],
            }
        )
    )
    devices_path.write_text(
        json.dumps(
            [
                {
                    "id": "thermostat-device",
                    "name": "Bathroom Floor",
                    "key": "0123456789abcdef",
                    "category": "wk",
                    "mapping": {
                        "1": {
                            "code": "switch",
                            "type": "Boolean",
                            "values": {},
                        },
                        "2": {
                            "code": "temp_set",
                            "type": "Integer",
                            "values": {"unit": "\u00b0C", "min": 10, "max": 70, "scale": 1, "step": 5},
                        },
                        "6": {
                            "code": "child_lock",
                            "type": "Boolean",
                            "values": {},
                        },
                        "5": {
                            "code": "eco",
                            "type": "Boolean",
                            "values": {},
                        },
                        "3": {
                            "code": "upper_temp",
                            "type": "Integer",
                            "values": {"unit": "\u00b0C", "min": 0, "max": 100, "scale": 0, "step": 5},
                        },
                    },
                }
            ]
        )
    )

    config = load_config(str(config_path))

    [device] = config["devices"]
    assert device["profile"] == "thermostat"
    assert device["mappings"] == {
        "power": {"dps": "1", "type": "boolean"},
        "target_temperature": {
            "dps": "2",
            "type": "integer",
            "scale": 2,
            "min": 5,
            "max": 35,
            "step": 0.5,
            "unit": "\u00b0C",
        },
        "child_lock": {"dps": "6", "type": "boolean"},
        "eco": {"dps": "5", "type": "boolean"},
        "ambient_temperature": {
            "dps": "3",
            "type": "integer",
            "scale": 2,
            "min": 0,
            "max": 50,
            "step": 5,
            "unit": "\u00b0C",
        },
        "current_temperature": {"dps": "102", "type": "integer", "scale": 2, "unit": "\u00b0C"},
        "sensor_mode": {"dps": "103", "type": "string"},
        "thermostat_active": {"dps": "104", "type": "boolean"},
    }


def test_kettle_auto_mapping_uses_bh_category(tmp_path):
    config_path = tmp_path / "config.yaml"
    devices_path = tmp_path / "devices.json"

    config_path.write_text(
        yaml.safe_dump(
            {
                "mqtt": {"host": "localhost"},
                "bridge": {},
                "devices": [{"id": "kettle-device", "ip": "192.168.1.111"}],
            }
        )
    )
    devices_path.write_text(
        json.dumps(
            [
                {
                    "id": "kettle-device",
                    "name": "Kettle",
                    "key": "0123456789abcdef",
                    "category": "bh",
                    "version": "3.5",
                    "product_name": "HEATROW 2023",
                    "mapping": {
                        "1": {"code": "start", "type": "Boolean", "values": {}},
                        "2": {
                            "code": "temp_current",
                            "type": "Integer",
                            "values": {"unit": "\u00b0C", "min": 0, "max": 100, "scale": 0, "step": 1},
                        },
                        "4": {
                            "code": "temp_set",
                            "type": "Integer",
                            "values": {"unit": "\u00b0C", "min": 0, "max": 100, "scale": 0, "step": 1},
                        },
                        "7": {
                            "code": "warm_time",
                            "type": "Integer",
                            "values": {"unit": "min", "min": 0, "max": 720, "scale": 0, "step": 1},
                        },
                        "8": {
                            "code": "status",
                            "type": "Enum",
                            "values": {"range": ["standby", "heating", "cooling", "warm"]},
                        },
                        "9": {
                            "code": "work_type",
                            "type": "Enum",
                            "values": {"range": ["boiling_quick"]},
                        },
                        "12": {
                            "code": "countdown",
                            "type": "Integer",
                            "values": {"unit": "min", "min": 0, "max": 720, "scale": 0, "step": 1},
                        },
                        "13": {
                            "code": "countdown_left",
                            "type": "Integer",
                            "values": {"unit": "min", "min": 0, "max": 720, "scale": 0, "step": 1},
                        },
                        "14": {"code": "warm", "type": "Boolean", "values": {}},
                    },
                }
            ]
        )
    )

    config = load_config(str(config_path))

    [device] = config["devices"]
    assert device["profile"] == "kettle"
    assert device["version"] == "3.5"
    assert device["product_name"] == "HEATROW 2023"
    assert device["mappings"] == {
        "power": {"dps": "1", "type": "boolean"},
        "current_temperature": {
            "dps": "2",
            "type": "integer",
            "min": 0,
            "max": 100,
            "step": 1,
            "unit": "\u00b0C",
        },
        "target_temperature": {
            "dps": "4",
            "type": "integer",
            "min": 0,
            "max": 100,
            "step": 1,
            "unit": "\u00b0C",
        },
        "warm_time": {"dps": "7", "type": "integer", "min": 0, "max": 720, "step": 1, "unit": "min"},
        "status": {
            "dps": "8",
            "type": "enum",
            "values": {"standby": "standby", "heating": "heating", "cooling": "cooling", "warm": "warm"},
        },
        "work_type": {"dps": "9", "type": "enum", "values": {"boiling_quick": "boiling_quick"}},
        "countdown": {"dps": "12", "type": "integer", "min": 0, "max": 720, "step": 1, "unit": "min"},
        "countdown_left": {"dps": "13", "type": "integer", "min": 0, "max": 720, "step": 1, "unit": "min"},
        "warm": {"dps": "14", "type": "boolean"},
    }


def test_profile_mismatch_with_devices_json_category_is_warned(tmp_path, caplog):
    config_path = tmp_path / "config.yaml"
    devices_path = tmp_path / "devices.json"

    config_path.write_text(
        yaml.safe_dump(
            {
                "mqtt": {"host": "localhost"},
                "bridge": {},
                "devices": [
                    {
                        "id": "kettle-device",
                        "ip": "192.168.1.111",
                        "profile": "thermostat",
                    }
                ],
            }
        )
    )
    devices_path.write_text(
        json.dumps(
            [
                {
                    "id": "kettle-device",
                    "name": "Kettle",
                    "key": "0123456789abcdef",
                    "category": "bh",
                    "mapping": {"1": {"code": "start", "type": "Boolean", "values": {}}},
                }
            ]
        )
    )

    config = load_config(str(config_path))

    [device] = config["devices"]
    assert device["profile"] == "thermostat"
    assert "category bh maps to profile=kettle" in caplog.text
