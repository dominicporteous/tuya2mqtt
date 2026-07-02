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
                    "category": "cz",
                    "mapping": {
                        "1": {
                            "code": "switch",
                            "type": "Boolean",
                            "values": {},
                        }
                    },
                }
            ]
        )
    )

    config = load_config(str(config_path))

    [device] = config["devices"]
    assert device["profile"] == "plug"
    assert device["mappings"] == {"switch": {"dps": "1", "type": "boolean"}}
