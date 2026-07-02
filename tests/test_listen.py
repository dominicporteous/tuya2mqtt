from tuya2mqtt_local.modes.listen import listen_mode


def test_listen_json_output_suppresses_startup_banner(monkeypatch, capsys):
    class FakeClient:
        def __init__(self, device_config):
            self.status_calls = 0

        def status(self):
            self.status_calls += 1
            if self.status_calls == 1:
                return {"1": False}
            raise KeyboardInterrupt

    monkeypatch.setattr("tuya2mqtt_local.modes.listen.TuyaClient", FakeClient)
    monkeypatch.setattr("tuya2mqtt_local.modes.listen.time.sleep", lambda interval: None)

    listen_mode(
        {
            "mqtt": {"host": "localhost"},
            "devices": [
                {
                    "key": "office-plug",
                    "id": "bf1234567890abcdef",
                    "ip": "192.168.0.55",
                }
            ],
        },
        "office-plug",
        json_output=True,
    )

    assert capsys.readouterr().out == ""
