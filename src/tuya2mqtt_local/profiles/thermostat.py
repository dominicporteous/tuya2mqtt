import logging

from typing import Any, Optional
from .base import DeviceProfile

logger = logging.getLogger(__name__)


class ThermostatProfile(DeviceProfile):
    @property
    def name(self) -> str:
        return "thermostat"

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

        if "power" in state:
            state["hvac_mode"] = "heat" if state["power"] else "off"

        return state

    def command_to_dps(self, command: str, payload: str, mappings: dict[str, Any]) -> list[tuple[Optional[str], Any]]:
        if command == "hvac_mode":
            power_mapping = mappings.get("power")
            if not power_mapping:
                return []
            return [(power_mapping["dps"], payload != "off")]

        if command in mappings:
            mapping = mappings[command]
            dps_id = mapping["dps"]
            logger.info(f"Mapping command {command} to DPS {dps_id} with payload {payload}")

            if command in ("power", "child_lock", "eco"):
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

        return []

    def discovery_components(self, device_config: dict[str, Any], mqtt_config: dict[str, Any]) -> dict[str, Any]:
        mappings = device_config.get("mappings", {})
        device_name = device_config.get("name", "Unknown Tuya Thermostat")

        components = {}

        if "power" in mappings and "target_temperature" in mappings:
            m_temp = mappings["target_temperature"]
            climate = {
                "p": "climate",
                "unique_id": f"tuya_{device_config['key']}_climate",
                "name": None,
                "mode_cmd_t": "~/set/hvac_mode",
                "mode_stat_t": "~/state",
                "mode_stat_tpl": "{{ value_json.hvac_mode }}",
                "modes": ["off", "heat"],
                "temp_cmd_t": "~/set/target_temperature",
                "temp_stat_t": "~/state",
                "temp_stat_tpl": "{{ value_json.target_temperature | float }}",
                "temp_unit": "C" if "C" in m_temp.get("unit", "C") else "F",
                "min_temp": m_temp.get("min", 10),
                "max_temp": m_temp.get("max", 70),
                "temp_step": m_temp.get("step", 1),
                "stat_t": "~/state",
                "avty_t": "~/availability",
            }

            if "current_temperature" in mappings:
                climate["curr_temp_t"] = "~/state"
                climate["curr_temp_tpl"] = "{{ value_json.current_temperature | float }}"

            components["climate"] = climate

        if "eco" in mappings:
            components["eco"] = {
                "p": "switch",
                "unique_id": f"tuya_{device_config['key']}_eco",
                "name": f"{device_name} Eco",
                "cmd_t": "~/set/eco",
                "pl_on": "ON",
                "pl_off": "OFF",
                "stat_on": "ON",
                "stat_off": "OFF",
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{% if value_json.eco %}ON{% else %}OFF{% endif %}"
            }

        if "child_lock" in mappings:
            components["child_lock"] = {
                "p": "switch",
                "unique_id": f"tuya_{device_config['key']}_child_lock",
                "name": f"{device_name} Child Lock",
                "cmd_t": "~/set/child_lock",
                "pl_on": "ON",
                "pl_off": "OFF",
                "stat_on": "ON",
                "stat_off": "OFF",
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{% if value_json.child_lock %}ON{% else %}OFF{% endif %}"
            }

        if "ambient_temperature" in mappings:
            components["ambient_temperature"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_ambient_temperature",
                "name": f"{device_name} Ambient Temperature",
                "dev_cla": "temperature",
                "unit_of_meas": mappings["ambient_temperature"].get("unit", "\u00b0C"),
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.ambient_temperature }}"
            }

        if "sensor_mode" in mappings:
            components["sensor_mode"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_sensor_mode",
                "name": f"{device_name} Sensor Mode",
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.sensor_mode }}"
            }

        if "thermostat_active" in mappings:
            components["thermostat_active"] = {
                "p": "binary_sensor",
                "unique_id": f"tuya_{device_config['key']}_thermostat_active",
                "name": f"{device_name} Active",
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{% if value_json.thermostat_active %}ON{% else %}OFF{% endif %}"
            }

        return components
