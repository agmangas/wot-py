<!-- Copyright (c) 2026 Contributors to the Eclipse Foundation -->

# Basic Security Test

A minimal two-script example that demonstrates HTTP Basic authentication (username + password) on a WoT Thing using CoAP.

## Files

| File | Role |
|------|------|
| `test.py` | Exposes a Thing secured with `basic` scheme over CoAP |
| `test-client.py` | Consumes the Thing using stored credentials |

## Running

**Terminal 1 — server**

```bash
.venv/bin/python examples/basic-security-test/test.py
```

The server starts a CoAP binding on port `5683` and a TD catalogue on port `9090`.
Credentials are hardcoded: username `user`, password `pass`.

**Terminal 2 — client**

```bash
.venv/bin/python examples/basic-security-test/test-client.py
```

## What it demonstrates

- Declaring a `basic` `securityDefinitions` scheme in a TD
- Passing credentials to `Servient.add_credentials`
- Consuming a secured Thing from a client with matching credentials
