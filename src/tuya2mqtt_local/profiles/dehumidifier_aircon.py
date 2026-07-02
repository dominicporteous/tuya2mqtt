import logging

from typing import Any, Optional
from .base import DeviceProfile

logger = logging.getLogger(__name__)

class DehumidifierAirconProfile(DeviceProfile):
    @property
    def name(self) -> str:
        return "dehumidifier_aircon"

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

        # Handle HVAC Mode (combined Power + Mode)
        power_mapping = mappings.get("power")
        mode_mapping = mappings.get("mode")
        if power_mapping and mode_mapping:
            is_on = self._get_mapped_value(power_mapping["dps"], raw_dps, power_mapping)
            if is_on:
                state["hvac_mode"] = state.get("mode", "auto")
            else:
                state["hvac_mode"] = "off"

        return state

    def command_to_dps(self, command: str, payload: str, mappings: dict[str, Any]) -> list[tuple[Optional[str], Any]]:
        # Handle HVAC Mode command
        if command == "hvac_mode":
            power_mapping = mappings.get("power")
            mode_mapping = mappings.get("mode")
            if not power_mapping or not mode_mapping:
                return []
            
            if payload == "off":
                return [(power_mapping["dps"], False)]
            else:
                # Send power ON followed by mode change
                return [
                    (power_mapping["dps"], True),
                    (mode_mapping["dps"], self._reverse_map_value(payload, mode_mapping))
                ]

        if command in mappings:
            mapping = mappings[command]
            dps_id = mapping["dps"]
            logger.info(f"Mapping command {command} to DPS {dps_id} with payload {payload}")
            
            # Handle special cases
            if command == "power":
                value = True if payload.upper() == "ON" else False
            elif command == "child_lock":
                value = True if payload.upper() == "ON" else False
            else:
                try:
                    # Try to parse as int/float if it looks like one
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
        device_name = device_config.get("name", "Unknown Tuya Dehumidifier")
        
        components = {}
        
        # Unified Climate Entity
        if "mode" in mappings and "target_temperature" in mappings:
            modes = ["off"] + list(mappings["mode"].get("values", {}).values())
            m_temp = mappings["target_temperature"]
            climate = {
                "p": "climate",
                "unique_id": f"tuya_{device_config['key']}_climate",
                "name": None,
                "mode_cmd_t": "~/set/hvac_mode",
                "mode_stat_t": "~/state",
                "mode_stat_tpl": "{{ value_json.hvac_mode }}",
                "modes": modes,
                "curr_temp_t": "~/state",
                "curr_temp_tpl": "{{ value_json.current_temperature | float }}",
                "temp_cmd_t": "~/set/target_temperature",
                "temp_stat_t": "~/state",
                "temp_stat_tpl": "{{ value_json.target_temperature | float }}",
                "temp_unit": "C" if "C" in m_temp.get("unit", "C") else "F",
                "min_temp": m_temp.get("min", 16),
                "max_temp": m_temp.get("max", 30),
                "temp_step": m_temp.get("step", 1),
                "stat_t": "~/state",
                "avty_t": "~/availability",
            }

            if "fan_mode" in mappings:
                climate["fan_modes"] = list(mappings["fan_mode"].get("values", {}).values())
                climate["fan_mode_cmd_t"] = "~/set/fan_mode"
                climate["fan_mode_stat_t"] = "~/state"
                climate["fan_mode_stat_tpl"] = "{{ value_json.fan_mode }}"

            components["climate"] = climate

        # Keep separate sensors for humidity if present
        if "current_humidity" in mappings:
            components["current_humidity"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_current_humidity",
                "name": f"{device_name} Current Humidity",
                "dev_cla": "humidity",
                "unit_of_meas": mappings["current_humidity"].get("unit", "%"),
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.current_humidity }}"
            }

        if "target_humidity" in mappings:
            m = mappings["target_humidity"]
            components["target_humidity"] = {
                "p": "number",
                "unique_id": f"tuya_{device_config['key']}_target_humidity",
                "name": f"{device_name} Target Humidity",
                "cmd_t": "~/set/target_humidity",
                "min": m.get("min", 30),
                "max": m.get("max", 80),
                "step": m.get("step", 5),
                "unit_of_meas": m.get("unit", "%"),
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.target_humidity }}"
            }

        if "power" in mappings:
            components["power"] = {
                "p": "switch",
                "unique_id": f"tuya_{device_config['key']}_power",
                "name": f"{device_name} Power",
                "cmd_t": "~/set/power",
                "pl_on": "ON",
                "pl_off": "OFF",
                "stat_on": "ON",
                "stat_off": "OFF",
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{% if value_json.power %}ON{% else %}OFF{% endif %}"
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

        return components
