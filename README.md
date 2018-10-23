# W3C WoT Python

## Introduction

This repository contains an experimental implementation of a [W3C WoT Runtime](https://github.com/w3c/wot-architecture/blob/master/terminology.md#wot-runtime) and the [W3C WoT Scripting API](https://w3c.github.io/wot-scripting-api/) in Python.

Inspired by the exploratory implementations located in the [thingweb GitHub page](https://github.com/thingweb).

## Features

* Supports Python 2.7, 3.6 and 3.7.
* Fully-implemented `WoT` interface.
* Asynchronous I/O programming model based on coroutines.

> WoTPy uses the [Tornado Framework](https://www.tornadoweb.org) to enable coroutines in Python 2.7. Python 3 applications may use the built-in package `asyncio`.

* Client and server [Protocol Binding](https://github.com/w3c/wot-architecture/blob/master/terminology.md#protocol-binding) implementations for HTTP, CoAP, WebSockets and MQTT.

## ToDo
# W3C WoT Python

## Introduction

This repository contains an experimental implementation of a [W3C WoT Runtime](https://github.com/w3c/wot-architecture/blob/master/terminology.md#wot-runtime) and the [W3C WoT Scripting API](https://w3c.github.io/wot-scripting-api/) in Python.

Inspired by the exploratory implementations located in the [thingweb GitHub page](https://github.com/thingweb).

## Features

* Supports Python 2.7, 3.6 and 3.7.
* Fully-implemented `WoT` interface.
* Asynchronous I/O programming model based on coroutines.

> WoTPy uses the [Tornado Framework](https://www.tornadoweb.org) to enable coroutines in Python 2.7. Python 3 applications may use the built-in package `asyncio`.

* Multiple client and server [Protocol Binding](https://github.com/w3c/wot-architecture/blob/master/terminology.md#protocol-binding) implementations.

|   Protocol | Implementation based on                                     | Python 2                 | Python 3           | R/W Property       | Observe Property   | Invoke Action      | Subscribe to Event |
|-----------:|-------------------------------------------------------------|--------------------------|--------------------|--------------------|--------------------|--------------------|--------------------|
| HTTP       | [tornadoweb/tornado](https://github.com/tornadoweb/tornado) | :heavy_check_mark:       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| WebSockets | [tornadoweb/tornado](https://github.com/tornadoweb/tornado) | :heavy_check_mark:       | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| CoAP       | [chrysn/aiocoap](https://github.com/chrysn/aiocoap)         | :heavy_multiplication_x: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |
| MQTT       | [beerfactory/hbmqtt](https://github.com/beerfactory/hbmqtt) | :heavy_multiplication_x: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: | :heavy_check_mark: |

## ToDo

* Thing discovery.
* Subscription to Thing Description changes.

## Development

Install in development mode:

```
pip install -U -e .[tests]
```

To run the tests in both Python 2 and Python 3 environments:

```
tox
```

### Building the docs

Move to the `docs` folder and run:

```
make html
```
* Thing discovery.
* Subscription to Thing Description changes.

## Development

Install in development mode:

```
pip install -U -e .[tests]
```

To run the tests in both Python 2 and Python 3 environments:

```
tox
```

### Building the docs

Move to the `docs` folder and run:

```
make html
```