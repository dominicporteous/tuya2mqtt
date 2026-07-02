import click
import logging
from .config import load_config
from .util import setup_logging, redact_config
from .modes.bridge import BridgeMode
from .modes.listen import listen_mode
from .modes.wizard import wizard_mode
from .modes.dump import dump_mode
from .modes.scan import scan_mode

@click.group()
def cli():
    """tuya2mqtt CLI."""
    pass

@cli.command()
@click.option("--config", required=True, type=click.Path(exists=True), help="Path to config.yaml")
def bridge(config):
    """Run the MQTT bridge."""
    cfg = load_config(config)
    setup_logging(cfg["bridge"].get("log_level", "info"))
    
    # Redact config for logging
    redacted = redact_config(cfg)
    logging.getLogger("tuya2mqtt_local").debug(f"Loaded config: {redacted}")
    
    bridge_service = BridgeMode(cfg)
    bridge_service.run()

@cli.command()
@click.option("--config", required=True, type=click.Path(exists=True), help="Path to config.yaml")
@click.option("--device", required=True, help="Device key from config")
@click.option("--interval", default=1.0, help="Polling interval in seconds")
@click.option("--json", "json_output", is_flag=True, help="Output JSON")
@click.option("--mqtt-debug", is_flag=True, help="Publish observed changes to MQTT debug topic")
@click.option("--show-unchanged", is_flag=True, help="Show log line even when no changes")
@click.option("--duration", default=0, help="Duration to listen in seconds (0 for indefinite)")
def listen(config, device, interval, json_output, mqtt_debug, show_unchanged, duration):
    """Listen for DPS changes."""
    cfg = load_config(config)
    setup_logging("error")  # Minimize noise in listen mode
    listen_mode(cfg, device, interval, duration, json_output, mqtt_debug, show_unchanged)

@cli.command()
@click.option("--output-dir", type=click.Path(), help="Directory to save wizard results")
def wizard(output_dir):
    """Run TinyTuya wizard for provisioning."""
    wizard_mode(output_dir)

@cli.command(context_settings={"ignore_unknown_options": True, "allow_extra_args": True})
@click.argument("args", nargs=-1, type=click.UNPROCESSED)
def scan(args):
    """Run TinyTuya scan, forwarding any extra args."""
    scan_mode(args)

@cli.command()
@click.option("--config", required=True, type=click.Path(exists=True), help="Path to config.yaml")
@click.option("--device", required=True, help="Device key from config")
def dump(config, device):
    """One-shot raw status dump."""
    cfg = load_config(config)
    dump_mode(cfg, device)

def main():
    cli()

if __name__ == "__main__":
    main()
