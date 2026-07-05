import logging
import time
from typing import Any
from ..mqtt import MqttClient
from ..tuya import TuyaClient
from ..profiles import get_profile
from ..discovery import publish_discovery

logger = logging.getLogger(__name__)

class BridgeMode:
    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.devices: dict[str, dict[str, Any]] = {}
        
        exit_on_command_error = config["bridge"].get("exit_on_command_error", True)
        exit_on_status_error = config["bridge"].get("exit_on_status_error", False)
        
        for device_config in config["devices"]:
            key = device_config["key"]
            
            # Ensure mappings are present in the config passed to the client
            if "mappings" not in device_config:
                logger.error(f"Device {device_config.get('name', key)} missing 'mappings' key! Searching for match...")
                # Attempt to look up the mapping manually from config if bridge didn't get it
                # Assuming config.py is where loading happened, we could technically re-scan or look at loaded supplemental info
                # But for now, ensuring the object is fully passed is the priority.
            
            self.devices[key] = {
                "config": device_config,
                "client": TuyaClient(
                    device_config,
                    exit_on_command_error=exit_on_command_error,
                    exit_on_status_error=exit_on_status_error,
                ),
                "profile": get_profile(device_config["profile"]),
                "last_state": {},
                "online": False
            }

        self.mqtt = MqttClient(
            config["mqtt"],
            on_command=self.handle_command,
            on_connect=self.on_mqtt_connect
        )

    def on_mqtt_connect(self):
        # Republish discovery and state for all devices
        logger.info("MQTT connected, publishing discovery and availability")
        publish_discovery(self.mqtt, self.config)
        for key in self.devices:
            self.publish_availability(key)

    @staticmethod
    def _device_label(device_key: str, device: dict[str, Any]) -> str:
        device_config = device.get("config", {})
        device_name = device_config.get("name")
        if device_name:
            return f"{device_name} ({device_key})"
        return device_key

    def handle_command(self, device_key: str, command: str, payload: str):
        if device_key not in self.devices:
            logger.warning(f"Received command for unknown device: {device_key}")
            return
        
        device = self.devices[device_key]
        device_label = self._device_label(device_key, device)
        profile = device["profile"]
        if not profile:
            logger.warning(f"No profile for device: {device_label}")
            return

        try:
            if command.startswith("dps/"):
                logging.getLogger(__name__).info(f"Handling dps {command} for {device_label}")
                dps_id = command.split("/")[1]
                # Try to parse payload as JSON, fallback to string
                try:
                    import json
                    value = json.loads(payload)
                except ValueError:
                    from ..util import parse_raw_value
                    value = parse_raw_value(payload)
                device["client"].set_dps(dps_id, value)
            else:
                logging.getLogger(__name__).info(f"Handling non-dps {command} for {device_label}")
                updates = profile.command_to_dps(command, payload, device["config"].get("mappings", {}))
                if updates:
                    for dps_id, value in updates:
                        if dps_id:
                            device["client"].set_dps(dps_id, value)
                    
                    # Optimistic update: trigger a state refresh
                    time.sleep(1) # Allow device time to process
                    raw_dps = device["client"].status()
                    if raw_dps:
                        self.publish_state(device_key, raw_dps)
                else:
                    logging.getLogger(__name__).warning(f"Profile {profile.name} could not map command {command} for {device_label}")
        except Exception as e:
            logging.getLogger(__name__).error(f"Error handling command {command} for {device_label}: {e}")
        

    def publish_availability(self, device_key: str):
        device = self.devices[device_key]
        base_topic = f"{self.config['mqtt'].get('base_topic', 'tuya')}/{device_key}"
        availability = "online" if device["client"].is_online() else "offline"
        self.mqtt.publish(f"{base_topic}/availability", availability, retain=True)

    def publish_state(self, device_key: str, raw_dps: dict[str, Any]):
        device = self.devices[device_key]
        profile = device["profile"]
        if not profile:
            return

        state = profile.normalize_state(raw_dps, device["config"].get("mappings", {}))
        logger.info(f"Publishing state for {self._device_label(device_key, device)}: {state}")
        
        # Add raw DPS if requested
        if device["config"].get("mappings", {}).get("raw", {}).get("include_unmapped"):
            state["raw_dps"] = raw_dps
        
        base_topic = f"{self.config['mqtt'].get('base_topic', 'tuya')}/{device_key}"
        self.mqtt.publish(f"{base_topic}/state", state, retain=self.config["mqtt"].get("retain_state", False))
        
        # If requested, also publish to debug topic
        if device["config"].get("mappings", {}).get("raw", {}).get("include_unmapped"):
             self.mqtt.publish(f"{base_topic}/debug/raw", raw_dps)

    def run(self):
        self.mqtt.connect()
        poll_interval = self.config["bridge"].get("poll_interval_seconds", 5)
        
        logger.info("Bridge started, entering main loop")
        while True:
            for key, device in self.devices.items():
                try:
                    logger.info(f"Polling device {self._device_label(key, device)}")

                    raw_dps = device["client"].status()
                    current_online = device["client"].is_online()
                    
                    if current_online != device["online"]:
                        device["online"] = current_online
                        self.publish_availability(key)
                        
                    if raw_dps:
                        self.publish_state(key, raw_dps)
                except Exception as e:
                    logger.error(f"Error polling device {self._device_label(key, device)}: {e}")
            
            time.sleep(poll_interval)
