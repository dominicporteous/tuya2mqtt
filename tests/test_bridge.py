from tuya2mqtt_local.modes.bridge import BridgeMode
from tuya2mqtt_local.profiles.plug import PlugProfile


class FakeClient:
    def __init__(self, online=True):
        self.online = online

    def is_online(self):
        return self.online


class FakeMqtt:
    def __init__(self):
        self.messages = []

    def publish(self, topic, payload, retain=False):
        self.messages.append((topic, payload, retain))


def test_bridge_publish_availability_defaults_base_topic():
    bridge = BridgeMode.__new__(BridgeMode)
    bridge.config = {"mqtt": {}}
    bridge.devices = {"office-plug": {"client": FakeClient(online=True)}}
    bridge.mqtt = FakeMqtt()

    bridge.publish_availability("office-plug")

    assert bridge.mqtt.messages == [("tuya/office-plug/availability", "online", True)]


def test_bridge_publish_state_defaults_base_topic():
    bridge = BridgeMode.__new__(BridgeMode)
    bridge.config = {"mqtt": {}}
    bridge.devices = {
        "office-plug": {
            "config": {"mappings": {"switch": {"dps": "1"}}},
            "profile": PlugProfile(),
        }
    }
    bridge.mqtt = FakeMqtt()

    bridge.publish_state("office-plug", {"1": True})

    assert bridge.mqtt.messages == [("tuya/office-plug/state", {"power": True}, False)]
