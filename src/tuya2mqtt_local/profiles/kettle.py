import logging
from typing import Any, Optional

from .base import DeviceProfile

logger = logging.getLogger(__name__)


class KettleProfile(DeviceProfile):
    @property
    def name(self) -> str:
        return "kettle"

    def normalize_state(self, raw_dps: dict[str, Any], mappings: dict[str, Any]) -> dict[str, Any]:
        state = {}
        for key, mapping in mappings.items():
            if key == "raw":
                continue

            dps_id = mapping.get("dps")
            if dps_id:
                val = self._get_mapped_value(dps_id, raw_dps, mapping)
                if val is not None:
                    state[key] = val

        return state

    def command_to_dps(self, command: str, payload: str, mappings: dict[str, Any]) -> list[tuple[Optional[str], Any]]:
        if command not in mappings:
            return []

        mapping = mappings[command]
        dps_id = mapping["dps"]
        logger.info(f"Mapping command {command} to DPS {dps_id} with payload {payload}")

        if command in ("power", "warm"):
            value = payload.upper() == "ON"
        else:
            try:
                if "." in payload:
                    value = float(payload)
                else:
                    value = int(payload)
            except ValueError:
                value = payload

            value = self._reverse_map_value(value, mapping)

        return [(dps_id, value)]

    def discovery_components(self, device_config: dict[str, Any], mqtt_config: dict[str, Any]) -> dict[str, Any]:
        mappings = device_config.get("mappings", {})
        device_name = device_config.get("name", "Kettle")
        components = {}

        if "power" in mappings:
            components["power"] = self._switch_component(device_config, device_name, "power", "Power")

        if "warm" in mappings:
            components["warm"] = self._switch_component(device_config, device_name, "warm", "Warm")

        if "target_temperature" in mappings:
            components["target_temperature"] = self._number_component(
                device_config,
                device_name,
                "target_temperature",
                "Target Temperature",
                mappings["target_temperature"],
                0,
                100,
                1,
            )

        if "warm_time" in mappings:
            components["warm_time"] = self._number_component(
                device_config,
                device_name,
                "warm_time",
                "Warm Time",
                mappings["warm_time"],
                0,
                720,
                1,
            )

        if "countdown" in mappings:
            components["countdown"] = self._number_component(
                device_config,
                device_name,
                "countdown",
                "Countdown",
                mappings["countdown"],
                0,
                720,
                1,
            )

        if "current_temperature" in mappings:
            components["current_temperature"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_current_temperature",
                "name": f"{device_name} Current Temperature",
                "dev_cla": "temperature",
                "stat_cla": "measurement",
                "unit_of_meas": mappings["current_temperature"].get("unit", "\u00b0C"),
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.current_temperature }}",
            }

        if "countdown_left" in mappings:
            components["countdown_left"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_countdown_left",
                "name": f"{device_name} Countdown Left",
                "dev_cla": "duration",
                "stat_cla": "measurement",
                "unit_of_meas": mappings["countdown_left"].get("unit", "min"),
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.countdown_left }}",
            }

        if "status" in mappings:
            components["status"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_status",
                "name": f"{device_name} Status",
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.status }}",
            }

        if "work_type" in mappings:
            work_type = {
                "p": "select",
                "unique_id": f"tuya_{device_config['key']}_work_type",
                "name": f"{device_name} Work Type",
                "cmd_t": "~/set/work_type",
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.work_type }}",
            }
            options = list(mappings["work_type"].get("values", {}).values())
            if options:
                work_type["options"] = options
            components["work_type"] = work_type

        return components

    def _switch_component(
        self,
        device_config: dict[str, Any],
        device_name: str,
        key: str,
        name: str,
    ) -> dict[str, Any]:
        return {
            "p": "switch",
            "unique_id": f"tuya_{device_config['key']}_{key}",
            "name": f"{device_name} {name}",
            "cmd_t": f"~/set/{key}",
            "pl_on": "ON",
            "pl_off": "OFF",
            "stat_on": "ON",
            "stat_off": "OFF",
            "stat_t": "~/state",
            "avty_t": "~/availability",
            "val_tpl": f"{{% if value_json.{key} %}}ON{{% else %}}OFF{{% endif %}}",
        }

    def _number_component(
        self,
        device_config: dict[str, Any],
        device_name: str,
        key: str,
        name: str,
        mapping: dict[str, Any],
        default_min: int,
        default_max: int,
        default_step: int,
    ) -> dict[str, Any]:
        component = {
            "p": "number",
            "unique_id": f"tuya_{device_config['key']}_{key}",
            "name": f"{device_name} {name}",
            "cmd_t": f"~/set/{key}",
            "min": mapping.get("min", default_min),
            "max": mapping.get("max", default_max),
            "step": mapping.get("step", default_step),
            "stat_t": "~/state",
            "avty_t": "~/availability",
            "val_tpl": f"{{{{ value_json.{key} }}}}",
        }
        if "unit" in mapping:
            component["unit_of_meas"] = mapping["unit"]
        return component
