<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# Benchmark Example

A performance benchmarking suite that measures the throughput and latency of WoT interactions (property reads, action invocations, event subscriptions) over HTTP and WebSocket.

## Files

| File | Role |
|------|------|
| `server.py` | Exposes a Thing with benchmark-oriented interactions |
| `client.py` | Runs the benchmark against the server |
| `proxy.py` | Optional network proxy for latency/throughput measurement |
| `utils.py` | Shared utilities (argument parsing, result formatting) |
| `requirements.txt` | Extra dependencies for analysis and packet capture |

## Dependencies

```bash
.venv/bin/pip install -r examples/benchmark/requirements.txt
```

## Running

**Terminal 1 — server**

```bash
.venv/bin/python examples/benchmark/server.py
```

**Terminal 2 — client**

```bash
.venv/bin/python examples/benchmark/client.py --help
```

Use `--help` on the client to see available benchmark options (protocol, iteration count, interaction type).

## What it demonstrates

- High-volume property reads and action invocations
- Measuring round-trip latency across protocol bindings
- Using a proxy to add realistic network conditions
