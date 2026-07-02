# tuya2mqtt

A small Dockerized Python service that bridges local Tuya Wi-Fi devices into MQTT using Home Assistant MQTT Discovery, similar in spirit to Zigbee2MQTT.

## What it does

- **Local Control**: Uses TinyTuya for local communication. No Tuya cloud required at runtime.
- **MQTT Bridge**: Publishes device state and listens for commands via MQTT.
- **Home Assistant Discovery**: Automatically discovers devices in Home Assistant.
- **Listen Mode**: Interactive debug mode to observe DPS changes in real-time.
- **Provisioning Wizard**: Built-in TinyTuya wizard to get your local keys.
- **TinyTuya Scan**: Pass-through command for checking device IPs and protocol versions.

## What it does NOT do

- It does not make Tuya devices "standard"; it still uses Tuya-specific DPS modes and device mappings.
- It is not "plug and play"; still requires obtaining Local Keys (can be done via a wizard which relies one-time on Tuya cloud API keys).

## Provisioning Flow

To get your device local keys:

```bash
docker run -it --rm \
  -v ./config:/config \
  tuya2mqtt:latest \
  wizard --output-dir /config/tinytuya
```

Then copy the discovered ID, IP, and Local Key into `config.yaml`.

To scan your LAN for Tuya devices and protocol versions:

```bash
docker run -it --rm \
  --network host \
  -v ./config:/config \
  tuya2mqtt:latest \
  scan
```

## Configuration

Create a `config.yaml` based on `config.example.yaml`.

### Simple Configuration (Using `devices.json`)

If you have run the `wizard` and have a `devices.json` file in your configuration directory, you only need to provide the `id` and `ip` for each device. The bridge will automatically look up the `local_key`, `name`, and `profile` based on the Tuya category.

```yaml
devices:
  - id: bf1234567890abcdef
    ip: 192.168.0.55
```

The bridge currently supports auto-mapping these Tuya categories:

- `cz` (Socket/Plug) -> profile: `plug`
- `bh` (Kettle) -> profile: `kettle`
- `kt` (Air Conditioner) -> profile: `dehumidifier_aircon`
- `wk` (Thermostat) -> profile: `thermostat`

### Full Configuration

You can override any auto-discovered values or provide them manually:

```yaml
mqtt:
  host: 192.168.0.246
  discovery_prefix: homeassistant
  base_topic: tuya

devices:
  - key: office-plug
    name: "Custom Name"
    id: bf1234567890abcdef
    ip: 192.168.0.55
    local_key: abcdef0123456789
    version: "3.3"
    dev_type: default
    profile: plug
    mappings:
      switch:
        dps: "1"
```

### Troubleshooting Tuya Local Communication

If TinyTuya reports `Unexpected Payload from Device`, or logs an AES padding error after it
receives a response from the device, the usual next step is to test protocol and device type
settings. For example:

```yaml
devices:
  - key: bedroom-lamp
    name: Bedroom Lamp
    id: 05185026a4cf12d5f7b2
    ip: 192.168.0.55
    local_key: abcdef0123456789
    version: "3.4"
    dev_type: device22
    profile: plug
```

Try these combinations, restarting the bridge between each change:

- `version: "3.4"` with `dev_type: default`
- `version: "3.4"` with `dev_type: device22`
- `version: "3.5"` with `dev_type: default`
- `version: "3.3"` with `dev_type: device22`

Set `bridge.exit_on_status_error: false` while testing devices that intermittently close the
connection during status polling. The bridge will mark the device offline for that poll and retry
on the next interval instead of exiting.

Also confirm the configured IP belongs to the same physical device as the device ID, because DHCP
changes can produce the same decryption-looking error even when the local key is correct.

## Running

### Docker Compose

```yaml
services:
  tuya2mqtt:
    image: ghcr.io/OWNER/tuya2mqtt:latest
    network_mode: host
    volumes:
      - ./config:/config
```

```bash
docker compose up -d
```

### Listen Mode

Observe DPS changes while physically interacting with the device:

```bash
docker run -it --rm \
  --network host \
  -v ./config:/config \
  tuya2mqtt:latest \
  listen --config /config/config.yaml --device office-aircon
```

## MQTT Commands

```bash
# Toggle a switch
mosquitto_pub -h broker -t tuya/office-plug/set/switch -m ON

# Set climate mode
mosquitto_pub -h broker -t tuya/office-aircon/set/mode -m dry

# Set raw DPS
mosquitto_pub -h broker -t tuya/office-aircon/set/dps/1 -m true
```

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```
