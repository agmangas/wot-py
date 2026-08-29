<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# CPU Monitor Example

A server that exposes the host machine's CPU usage as a WoT Thing, with a configurable alert threshold event. Designed to run inside Docker alongside an MQTT broker.

## Files

| File | Role |
|------|------|
| `server.py` | Exposes a CPU Monitor Thing with properties and a CPU alert event |
| `requirements.txt` | Extra dependency: `psutil` |

## Dependencies

```bash
.venv/bin/pip install -r examples/cpumonitor/requirements.txt
```

## Running

```bash
.venv/bin/python examples/cpumonitor/server.py
```

Configuration via environment variables (all optional):

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT_CATALOGUE` | `9090` | TD catalogue port |
| `PORT_WS` | `9191` | WebSocket binding port |
| `PORT_HTTP` | `9292` | HTTP binding port |
| `MQTT_BROKER` | `mqtt://localhost` | MQTT broker URL |
| `CPU_THRESHOLD` | `50.0` | Alert threshold (%) |
| `CPU_CHECK_SEC` | `2.0` | Seconds between threshold checks |
| `CPU_UPDATE_SEC` | `1.0` | Seconds between CPU readings |

## What it demonstrates

- Configuring a Servient with three protocol bindings (HTTP, WebSocket, MQTT)
- Using environment variables for runtime configuration
- Running two independent asyncio loops (update + check) in parallel
- Emitting events when a sensor value crosses a threshold
