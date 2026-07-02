from typing import Optional
from .base import DeviceProfile
from .plug import PlugProfile
from .dehumidifier_aircon import DehumidifierAirconProfile
from .thermostat import ThermostatProfile

_PROFILES: dict[str, DeviceProfile] = {
    "plug": PlugProfile(),
    "dehumidifier_aircon": DehumidifierAirconProfile(),
    "thermostat": ThermostatProfile(),
}

def get_profile(name: str) -> Optional[DeviceProfile]:
    return _PROFILES.get(name)
