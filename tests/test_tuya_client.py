from tuya2mqtt_local.tuya import TuyaClient


def test_tuya_client_passes_connection_options(monkeypatch):
    created = {}

    class FakeDevice:
        def __init__(self, *args, **kwargs):
            created["args"] = args
            created["kwargs"] = kwargs
            self.version = None

        def set_version(self, version):
            self.version = version
            created["version"] = version

    monkeypatch.setattr("tuya2mqtt_local.tuya.tinytuya.Device", FakeDevice)

    TuyaClient(
        {
            "id": "bf1234567890abcdef",
            "ip": "192.168.0.55",
            "local_key": "abcdef0123456789",
            "name": "Office Plug",
            "version": "3.4",
            "dev_type": "device22",
            "connection_timeout_seconds": 7,
            "connection_retry_limit": 4,
            "connection_retry_delay_seconds": 2,
            "persist": True,
            "max_simultaneous_dps": 12,
            "profile": "plug",
        }
    )

    assert created["args"] == ("bf1234567890abcdef", "192.168.0.55", "abcdef0123456789")
    assert created["kwargs"] == {
        "dev_type": "device22",
        "connection_timeout": 7,
        "persist": True,
        "connection_retry_limit": 4,
        "connection_retry_delay": 2,
        "max_simultaneous_dps": 12,
    }
    assert created["version"] == 3.4
