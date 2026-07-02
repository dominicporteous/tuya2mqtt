import logging
from typing import Any
from .profiles import get_profile

logger = logging.getLogger(__name__)

def publish_discovery(mqtt_client: Any, config: dict[str, Any]):
    mqtt_config = config["mqtt"]
    discovery_prefix = mqtt_config.get("discovery_prefix", "homeassistant")
    retain = mqtt_config.get("retain_discovery", True)

    for device_config in config["devices"]:
        profile_name = device_config["profile"]
        profile = get_profile(profile_name)
        
        if not profile:
            logger.warning(f"No profile found for {profile_name}")
            continue

        device_key = device_config["key"]
        base_topic = f"{mqtt_config.get('base_topic', 'tuya')}/{device_key}"
        
        device_info = {
            "ids": [f"tuya_{device_config['id']}"],
            "name": device_config["name"],
            "mf": device_config.get("manufacturer", "Tuya"),
            "mdl": device_config.get("model", "Generic Device")
        }

        # Handle the specific case for the ID reported in the mesh
        # If the ID is the long string, we ensure the unique_id uses it consistently
        safe_id = device_config['id']
        
        origin_info = {
            "name": "tuya2mqtt",
            "sw": "0.1.0"
        }

        components = profile.discovery_components(device_config, mqtt_config)
        
        # In multi-topic discovery, we publish each component to its own topic
        # homeassistant/<component_type>/tuya_<safe_id>_<cmp_id>/config
        for cmp_id, cmp_config in components.items():
            component_type = cmp_config.get("p")
            if not component_type:
                continue
                
            # Create a copy to modify
            payload = cmp_config.copy()
            # Remove the 'p' (platform) key as it's part of the topic
            del payload["p"]
            
            # Ensure unique_id is truly unique and stable
            payload["unique_id"] = f"tuya_{safe_id}_{cmp_id}"
            
            # Add shared info
            payload["~"] = base_topic
            payload["dev"] = device_info
            payload["o"] = origin_info
            
            topic = f"{discovery_prefix}/{component_type}/tuya_{safe_id}_{cmp_id}/config"
            mqtt_client.publish(topic, payload, retain=retain)
            logger.info(f"Published discovery for {device_key} {component_type} ({cmp_id})")
