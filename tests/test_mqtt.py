from tuya2mqtt_local.mqtt import MqttClient


class FakeMessage:
    def __init__(self, topic, payload):
        self.topic = topic
        self.payload = payload.encode()


def test_mqtt_command_parser_handles_multi_segment_base_topic():
    commands = []
    mqtt = MqttClient(
        {"host": "localhost", "base_topic": "home/tuya"},
        on_command=lambda device_key, command, payload: commands.append((device_key, command, payload)),
    )

    mqtt._on_message(None, None, FakeMessage("home/tuya/office-plug/set/switch", "ON"))

    assert commands == [("office-plug", "switch", "ON")]


def test_mqtt_command_parser_handles_multi_segment_base_topic_dps_commands():
    commands = []
    mqtt = MqttClient(
        {"host": "localhost", "base_topic": "home/tuya"},
        on_command=lambda device_key, command, payload: commands.append((device_key, command, payload)),
    )

    mqtt._on_message(None, None, FakeMessage("home/tuya/office-plug/set/dps/1", "true"))

    assert commands == [("office-plug", "dps/1", "true")]


def test_mqtt_command_parser_ignores_topics_outside_base_topic():
    commands = []
    mqtt = MqttClient(
        {"host": "localhost", "base_topic": "home/tuya"},
        on_command=lambda device_key, command, payload: commands.append((device_key, command, payload)),
    )

    mqtt._on_message(None, None, FakeMessage("other/tuya/office-plug/set/switch", "ON"))

    assert commands == []
