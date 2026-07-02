from typing import Any, Optional
from .base import DeviceProfile

class PlugProfile(DeviceProfile):
    @property
    def name(self) -> str:
        return "plug"

    def normalize_state(self, raw_dps: dict[str, Any], mappings: dict[str, Any]) -> dict[str, Any]:
        state = {}
        if "switch" in mappings:
            state["power"] = raw_dps.get(mappings["switch"]["dps"])
        
        if "power" in mappings:
            state["power_w"] = self._get_mapped_value(mappings["power"]["dps"], raw_dps, mappings["power"])
            
        if "voltage" in mappings:
            state["voltage_v"] = self._get_mapped_value(mappings["voltage"]["dps"], raw_dps, mappings["voltage"])
            
        if "current" in mappings:
            state["current_a"] = self._get_mapped_value(mappings["current"]["dps"], raw_dps, mappings["current"])
            
        return state

    def command_to_dps(self, command: str, payload: str, mappings: dict[str, Any]) -> list[tuple[Optional[str], Any]]:
        if command == "switch" and "switch" in mappings:
            dps_id = mappings["switch"]["dps"]
            value = True if payload.upper() == "ON" else False
            return [(dps_id, value)]
        return []

    def discovery_components(self, device_config: dict[str, Any], mqtt_config: dict[str, Any]) -> dict[str, Any]:
        mappings = device_config.get("mappings", {})
        device_name = device_config.get("name", "Socket")
        
        components = {}
        
        if "switch" in mappings:
            components["switch"] = {
                "p": "switch",
                "unique_id": f"tuya_{device_config['key']}_switch",
                "name": None,  # Use device name
                "cmd_t": "~/set/switch",
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "pl_on": "ON",
                "pl_off": "OFF",
                "stat_on": "ON",
                "stat_off": "OFF",
                "val_tpl": "{% if value_json.power %}ON{% else %}OFF{% endif %}"
            }

        if "power" in mappings:
            components["power"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_power",
                "name": f"{device_name} Power",
                "dev_cla": "power",
                "stat_cla": "measurement",
                "unit_of_meas": mappings["power"].get("unit", "W"),
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.power_w }}"
            }

        if "voltage" in mappings:
            components["voltage"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_voltage",
                "name": f"{device_name} Voltage",
                "dev_cla": "voltage",
                "stat_cla": "measurement",
                "unit_of_meas": mappings["voltage"].get("unit", "V"),
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.voltage_v }}"
            }

        if "current" in mappings:
            components["current"] = {
                "p": "sensor",
                "unique_id": f"tuya_{device_config['key']}_current",
                "name": f"{device_name} Current",
                "dev_cla": "current",
                "stat_cla": "measurement",
                "unit_of_meas": mappings["current"].get("unit", "A"),
                "stat_t": "~/state",
                "avty_t": "~/availability",
                "val_tpl": "{{ value_json.current_a }}"
            }

        return components
