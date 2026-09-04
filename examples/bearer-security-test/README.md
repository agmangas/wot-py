<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# Bearer Security Test

A minimal two-script example that demonstrates Bearer token authentication on a WoT Thing using HTTP.

## Files

| File | Role |
|------|------|
| `test.py` | Exposes a Thing secured with `bearer` scheme over HTTP |
| `test-client.py` | Consumes the Thing using a stored token |

## Running

**Terminal 1 — server**

```bash
.venv/bin/python examples/bearer-security-test/test.py
```

The server starts an HTTP binding on port `9494` and a TD catalogue on port `9090`.
The token is hardcoded: `jg0ksz4nug1yf0ayi8ohf`.

**Terminal 2 — client**

```bash
.venv/bin/python examples/bearer-security-test/test-client.py
```

## What it demonstrates

- Declaring a `bearer` `securityDefinitions` scheme in a TD
- Passing a token to `Servient.add_credentials`
- Consuming a bearer-secured Thing from a client
