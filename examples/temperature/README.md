<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# Temperature Sensor Example

A server-only example that exposes a simulated temperature sensor Thing with a property, a threshold property, and a high-temperature event.

## Files

| File | Role |
|------|------|
| `server.py` | Exposes the temperature Thing and periodically updates/emits values |

## Running

```bash
.venv/bin/python examples/temperature/server.py
```

Endpoints started:

- `http://localhost:9090` — TD catalogue
- `http://localhost:9494` — HTTP binding
- `ws://localhost:9393` — WebSocket binding

Use the [subscriber example](../subscriber/) to consume observable properties and events from this Thing.

## What it demonstrates

- Custom property read handler (simulates async sensor retrieval)
- Periodic background tasks with `asyncio.create_task`
- Emitting events conditionally based on a configurable threshold property
- Running a Thing server indefinitely with `await asyncio.Future()`
