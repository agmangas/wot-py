<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# Subscriber Example

A generic consumer that subscribes to all observable properties and events on any Thing, given its TD URL.

## Files

| File | Role |
|------|------|
| `client.py` | Connects to a Thing and subscribes to all observables |

## Running

Start a Thing server first (e.g. the [temperature example](../temperature/)), then:

```bash
.venv/bin/python examples/subscriber/client.py \
    --url http://localhost:9090/urn:temperaturething \
    --time 60
```

- `--url` — full URL to the Thing Description (required)
- `--time` — how many seconds to listen before exiting (default: 120)

The TD URL can be found from the catalogue at `http://localhost:9090`.

## What it demonstrates

- Consuming a remote Thing from a TD URL with `WoT.consume_from_url`
- Introspecting a Thing's properties and events at runtime
- Subscribing to observable properties and events using the RxPY-style API
