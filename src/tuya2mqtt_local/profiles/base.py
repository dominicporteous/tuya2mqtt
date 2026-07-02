from typing import Any, Optional
from abc import ABC, abstractmethod

class DeviceProfile(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Profile name."""
        pass

    @abstractmethod
    def normalize_state(
        self, 
        raw_dps: dict[str, Any], 
        mappings: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert raw Tuya DPS to normalized state."""
        pass

    @abstractmethod
    def command_to_dps(
        self, 
        command: str, 
        payload: str, 
        mappings: dict[str, Any]
    ) -> list[tuple[Optional[str], Any]]:
        """Convert MQTT command and payload to a list of Tuya DPS ID and value pairs."""
        pass

    @abstractmethod
    def discovery_components(
        self, 
        device_config: dict[str, Any], 
        mqtt_config: dict[str, Any]
    ) -> dict[str, Any]:
        """Return Home Assistant discovery components."""
        pass

    def _get_mapped_value(self, dps_id: str, raw_dps: dict[str, Any], mapping: dict[str, Any]) -> Any:
        """Helper to get and scale/map a DPS value."""
        value = raw_dps.get(dps_id)
        if value is None:
            return None
        
        scale = mapping.get("scale")
        if scale and isinstance(value, (int, float)):
            value = value / scale
            
        values_map = mapping.get("values")
        if values_map and value in values_map:
            value = values_map[value]
            
        return value

    def _reverse_map_value(self, value: Any, mapping: dict[str, Any]) -> Any:
        """Helper to reverse map a value back to Tuya DPS value."""
        values_map = mapping.get("values")
        if values_map:
            for tt_val, ha_val in values_map.items():
                if ha_val == value:
                    return tt_val
        
        scale = mapping.get("scale")
        if scale and isinstance(value, (int, float)):
            return int(value * scale)
            
        return value