import logging
import json
import paho.mqtt.client as mqtt
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

class MqttClient:
    def __init__(
        self, 
        config: dict[str, Any], 
        on_command: Callable[[str, str, str], None],
        on_connect: Optional[Callable[[], None]] = None
    ):
        self.config = config
        self.on_command = on_command
        self.on_connect_cb = on_connect
        self.client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
            client_id=config.get("client_id", "tuya2mqtt")
        )
        
        if config.get("username"):
            self.client.username_pw_set(config["username"], config.get("password"))
            
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def connect(self):
        host = self.config["host"]
        port = self.config.get("port", 1883)
        logger.info(f"Connecting to MQTT broker at {host}:{port}")
        self.client.connect(host, port, 60)
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc, properties):
        if rc == 0:
            logger.info("Connected to MQTT broker")
            base_topic = self.config.get("base_topic", "tuya")
            # Subscribe to commands
            # <base_topic>/+/set/+
            # <base_topic>/+/set/dps/+
            client.subscribe(f"{base_topic}/+/set/#")
            
            # Subscribe to HA status
            birth_topic = self.config.get("birth_topic", "homeassistant/status")
            client.subscribe(birth_topic)
            
            if self.on_connect_cb:
                self.on_connect_cb()
        else:
            logger.error(f"Failed to connect to MQTT broker with code {rc}")

    def _on_disconnect(self, client, userdata, flags, rc, properties):
        logger.warning(f"Disconnected from MQTT broker with code {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            topic = msg.topic
            payload = msg.payload.decode()
            logger.debug(f"Received message: {topic} {payload}")
            
            birth_topic = self.config.get("birth_topic", "homeassistant/status")
            if topic == birth_topic:
                if payload == self.config.get("birth_payload", "online"):
                    logger.info("Home Assistant came online, triggering discovery republication")
                    if self.on_connect_cb:
                        self.on_connect_cb()
                return

            # tuya/<device_key>/set/<command>
            # tuya/<device_key>/set/dps/<dps_id>
            parts = topic.split("/")
            if len(parts) >= 4 and parts[2] == "set":
                device_key = parts[1]
                if parts[3] == "dps" and len(parts) >= 5:
                    command = f"dps/{parts[4]}"
                else:
                    command = parts[3]
                
                self.on_command(device_key, command, payload)
        except Exception as e:
            logger.error(f"Error handling MQTT message: {e}")

    def publish(self, topic: str, payload: Any, retain: bool = False):
        if not isinstance(payload, str):
            payload = json.dumps(payload)
        self.client.publish(topic, payload, retain=retain)