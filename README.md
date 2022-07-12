> :warning: Please note that this project is currently behind the current version of the W3C WoT specifications although **efforts are currently being made in order to bring this project back to date**.  
This actualization is still in the very early stages of development, so you may encounter bugs. Documentation may also be incomplete. Keep this in mind if you are planning on using this implementation on ongoing projects.

# WoTPy

[![Tests](https://img.shields.io/github/workflow/status/agmangas/wot-py/testing?label=tests)](https://github.com/agmangas/wot-py/actions/workflows/test-wot-py.yaml)
[![Coveralls](https://img.shields.io/coveralls/github/agmangas/wot-py)](https://coveralls.io/github/agmangas/wot-py)
[![PyPI](https://img.shields.io/pypi/v/wotpy)](https://pypi.org/project/wotpy/)

## Introduction

WoTPy is an experimental implementation of a [W3C WoT Runtime](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#wot-runtime) and the [W3C WoT Scripting API](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#scripting-api) in Python.

Inspired by the exploratory implementations located in the [thingweb GitHub page](https://github.com/thingweb).

## Features
- Supports Python 3 with versions >= 3.7
> :exclamation: Python 2 support is being dropped as it's reached its EOL.
- Fully-implemented `WoT` interface.
- Multicast discovery based on mDNS.
- Asynchronous I/O programming model based on coroutines.
- Multiple client and server [Protocol Binding](https://github.com/w3c/wot-architecture/blob/master/proposals/terminology.md#protocol-binding) implementations.

### Feature support matrix

|            Feature |  Python 3           | Implementation based on                                                 |
| -----------------: |  ------------------ | ----------------------------------------------------------------------- |
|       HTTP binding |  :heavy_check_mark: | [tornadoweb/tornado](https://github.com/tornadoweb/tornado)             |
| WebSockets binding |  :heavy_check_mark: | [tornadoweb/tornado](https://github.com/tornadoweb/tornado)             |
|       CoAP binding |  :heavy_check_mark: | [chrysn/aiocoap](https://github.com/chrysn/aiocoap)                     |
|       MQTT binding |  :warning: | [beerfactory/hbmqtt](https://github.com/beerfactory/hbmqtt)             |
|     mDNS discovery |  :heavy_check_mark: | [jstasiak/python-zeroconf](https://github.com/jstasiak/python-zeroconf) |

> :warning: Some of these features are not currently supported for all python versions since some of the dependecies are broken for versions higher than 3.7, such as `hbmqtt`.

## Couroutine APIs
> :warning: Tornado courutines will be replaced with the more up-to-date. [asyncio](https://docs.python.org/3/library/asyncio.html) module.

WoTPy is based on the [Tornado Framework](https://www.tornadoweb.org). Users therefore have two different API options to write code based on coroutines:

- Users on **Python 3** may use the native [asyncio](https://docs.python.org/3/library/asyncio.html) module. This is, in fact, the recommended approach. It should be noted that Tornado on Python 3 acts basically [as a wrapper](https://www.tornadoweb.org/en/stable/asyncio.html) around `asyncio`.

## Installation
> :warning: For the moment, this is not the current version, and it won't be  until we have reached some stability in the development.
```
pip install wotpy
```

### Development

To install in development mode with all the test dependencies:

```
pip install -U -e .[tests]
```

Some WoTPy features (e.g. CoAP binding) are not available outside of Linux. If you have Docker available in your system, and want to easily run the tests in a Linux environment (whether you're on macOS or Windows) you can use the Docker-based test script:

```
$ WOTPY_TESTS_MQTT_BROKER_URL=mqtt://192.168.1.141 ./pytest-docker-all.sh
...
+ docker run --rm -it -v /var/folders/zd/02pk7r3954s_t03lktjmvbdc0000gn/T/wotpy-547bed6bacf34ddc95b41eceb46553dd:/app -e WOTPY_TESTS_MQTT_BROKER_URL=mqtt://192.168.1.141 python:3.9 /bin/bash -c 'cd /app && pip install -U .[tests] && pytest -v --disable-warnings'
...
Python 3.7 :: OK
Python 3.8 :: OK
Python 3.9 :: OK
Python 3.10 :: OK
```
`WOTPY_TESTS_MQTT_BROKER_URL` defines the url of the MQTT broker. It will listen to port `1883` by default. If your broker is set up in a different way, you can provide the port in the url as well.

You can also test only for a specific Python version with the `PYTHON_TAG` variable and the `pytest-docker.sh` script like this:

```
$ WOTPY_TESTS_MQTT_BROKER_URL=mqtt://192.168.1.141 PYTHON_TAG=3.8 ./pytest-docker.sh
```
### Development in VSCode with devcontainers
We have also provided a convenient `devcontainer` configuration to better recreate your local development environment. VSCode should detect it if you have the [Remote - Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension installed.

## Docs
> :warning: Untested for current changes.

Move to the `docs` folder and run:

```
make html
```

If you attempt to build the docs on a non-Linux platform or with Python 2.7 `_autosummary` will complain about being unable to import the unsupported modules (e.g. MQTT on Python 2.7). In this case the docs will be missing the sections regarding unsupported features.
