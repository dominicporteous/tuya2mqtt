import subprocess
import sys

from click.testing import CliRunner

from tuya2mqtt_local.cli import cli
from tuya2mqtt_local.modes.scan import scan_mode


def test_scan_mode_passes_through_to_tinytuya(monkeypatch):
    calls = []

    def fake_run(cmd, check):
        calls.append({"cmd": cmd, "check": check})

    monkeypatch.setattr(subprocess, "run", fake_run)

    scan_mode(("-nocolor",))

    assert calls == [
        {
            "cmd": [sys.executable, "-m", "tinytuya", "scan", "-nocolor"],
            "check": True,
        }
    ]


def test_scan_cli_forwards_extra_args(monkeypatch):
    calls = []

    def fake_scan_mode(args):
        calls.append(args)

    monkeypatch.setattr("tuya2mqtt_local.cli.scan_mode", fake_scan_mode)

    result = CliRunner().invoke(cli, ["scan", "-nocolor"])

    assert result.exit_code == 0
    assert calls == [("-nocolor",)]
