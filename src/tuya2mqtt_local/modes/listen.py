import logging
import time
import json
from datetime import datetime
from typing import Any
from rich.console import Console
from rich.table import Table
from ..tuya import TuyaClient
from ..mqtt import MqttClient

logger = logging.getLogger(__name__)
console = Console()

def listen_mode(
    config: dict[str, Any], 
    device_key: str, 
    interval: float = 1.0, 
    duration: int = 0,
    json_output: bool = False,
    mqtt_debug: bool = False,
    show_unchanged: bool = False
):
    device_config = next((d for d in config["devices"] if d["key"] == device_key), None)
    
    mqtt_client = None
    if mqtt_debug:
        mqtt_client = MqttClient(config["mqtt"], on_command=lambda k, c, p: None)
        mqtt_client.connect()
        # Wait a bit for connection
        time.sleep(1)

    if not device_config:
        console.print(f"[red]Device {device_key} not found in config[/red]")
        return

    client = TuyaClient(device_config)
    if not json_output:
        console.print(f"Listening to {device_key} {device_config['id']} at {device_config['ip']}")
    
    initial_dps = client.status()
    if initial_dps is None:
        console.print("[red]Could not connect to device for initial status[/red]")
        return

    last_dps = initial_dps
    
    if not json_output:
        console.print("\nInitial DPS:")
        for dps_id, value in initial_dps.items():
            console.print(f"  {dps_id}: {repr(value)}")
        console.print("\nWaiting for changes (Press Ctrl+C to stop)...")

    start_time = time.time()
    try:
        while True:
            if duration > 0 and (time.time() - start_time) > duration:
                break
                
            time.sleep(interval)
            current_dps = client.status()
            if current_dps is None:
                continue

            changes = {}
            for dps_id, value in current_dps.items():
                old_value = last_dps.get(dps_id)
                if value != old_value:
                    changes[dps_id] = {"old": old_value, "new": value}

            if changes:
                ts = datetime.now().isoformat()
                
                if mqtt_client:
                    base_topic = config["mqtt"].get("base_topic", "tuya")
                    mqtt_client.publish(f"{base_topic}/{device_key}/debug/observed", {
                        "ts": ts,
                        "changes": changes
                    })

                if json_output:
                    print(json.dumps({
                        "device": device_key,
                        "ts": ts,
                        "changes": changes
                    }))
                else:
                    console.print(f"\n[bold]{ts} changed:[/bold]")
                    for dps_id, change in changes.items():
                        type_name = type(change['new']).__name__
                        console.print(f"  dps {dps_id}: {repr(change['old'])} -> {repr(change['new'])}   {type_name}")
                
                last_dps = current_dps
            elif show_unchanged and not json_output:
                 console.print(f"{datetime.now().isoformat()} - no changes")

    except KeyboardInterrupt:
        pass
