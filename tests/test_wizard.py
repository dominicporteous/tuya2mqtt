import subprocess
import sys

from tuya2mqtt_local.modes.wizard import wizard_mode


def test_wizard_uses_output_dir_as_working_directory(tmp_path, monkeypatch):
    calls = []

    def fake_run(cmd, check, cwd=None):
        calls.append({"cmd": cmd, "check": check, "cwd": cwd})
        (tmp_path / "tinytuya.json").write_text("{}")

    monkeypatch.setattr(subprocess, "run", fake_run)

    wizard_mode(str(tmp_path))

    assert calls == [
        {
            "cmd": [sys.executable, "-m", "tinytuya", "wizard"],
            "check": True,
            "cwd": str(tmp_path),
        }
    ]


def test_wizard_uses_current_directory_when_output_dir_is_omitted(monkeypatch):
    calls = []

    def fake_run(cmd, check, cwd=None):
        calls.append({"cmd": cmd, "check": check, "cwd": cwd})

    monkeypatch.setattr(subprocess, "run", fake_run)

    wizard_mode()

    assert calls == [
        {
            "cmd": [sys.executable, "-m", "tinytuya", "wizard"],
            "check": True,
            "cwd": None,
        }
    ]
