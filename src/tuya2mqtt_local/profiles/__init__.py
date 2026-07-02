from typing import Optional
from .base import DeviceProfile
from .plug import PlugProfile
from .dehumidifier_aircon import DehumidifierAirconProfile

_PROFILES: dict[str, DeviceProfile] = {
    "plug": PlugProfile(),
    "dehumidifier_aircon": DehumidifierAirconProfile(),
}

def get_profile(name: str) -> Optional[DeviceProfile]:
    return _PROFILES.get(name)