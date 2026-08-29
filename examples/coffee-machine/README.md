<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# Coffee Machine Example

A full producer/consumer pair demonstrating properties, actions, events, and catalogue-based discovery over HTTP and WebSockets.

## Files

| File | Role |
|------|------|
| `server.py` | Exposes the Smart Coffee Machine Thing |
| `client.py` | Consumes the Thing and exercises all interactions |

## Running

Open two terminals in the repository root.

**Terminal 1 — server**

```bash
.venv/bin/python examples/coffee-machine/server.py
```

Endpoints started:

- `http://localhost:9090` — TD catalogue
- `http://localhost:9494` — HTTP binding
- `ws://localhost:9393` — WebSocket binding

**Terminal 2 — client**

```bash
.venv/bin/python examples/coffee-machine/client.py
```

The client discovers the Thing URL from the catalogue automatically.

## What it demonstrates

- Producing a Thing from a TD dict and exposing it over multiple protocols
- Reading and writing properties
- Invoking actions with input/output
- Subscribing to observable properties and events
- Consuming a remote Thing via catalogue discovery
