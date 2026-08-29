#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2026 Contributors to the Eclipse Foundation
# Copyright (c) 2017 CTIC Centro Tecnologico
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
WoT application to expose a Thing that provides simulated temperature values.
"""

import asyncio
import json
import logging
import random

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

CATALOGUE_PORT = 9090
WEBSOCKET_PORT = 9393
HTTP_PORT = 9494

GLOBAL_TEMPERATURE = None
PERIODIC_MS = 3000
DEFAULT_TEMP_THRESHOLD = 27.0

LOGGER = logging.getLogger(__name__)

ID_THING = "urn:temperaturething"
NAME_PROP_TEMP = "temperature"
NAME_PROP_TEMP_THRESHOLD = "high-temperature-threshold"
NAME_EVENT_TEMP_HIGH = "high-temperature"

DESCRIPTION = {
    "id": ID_THING,
    "title": ID_THING,
    "@context": [
        "https://www.w3.org/2019/wot/td/v1",
    ],
    "securityDefinitions": {
        "nosec_sc":{
            "scheme":"nosec"
        }
    },
    "security": "nosec_sc",
    "properties": {
        NAME_PROP_TEMP: {
            "type": "number",
            "readOnly": True,
            "observable": True
        },
        NAME_PROP_TEMP_THRESHOLD: {
            "type": "number",
            "observable": True
        }
    },
    "events": {
        NAME_EVENT_TEMP_HIGH: {
            "data": {
                "type": "number"
            }
        }
    }
}


def update_temp():
    """Updates the global temperature value."""

    global GLOBAL_TEMPERATURE
    GLOBAL_TEMPERATURE = round(random.randint(20, 30) + random.random(), 2)
    LOGGER.info("Current temperature: {}".format(GLOBAL_TEMPERATURE))


async def emit_temp_high(exp_thing):
    """Emits a 'Temperature High' event if the temperature is over the threshold."""

    temp_threshold = await exp_thing.read_property(NAME_PROP_TEMP_THRESHOLD)

    if temp_threshold and GLOBAL_TEMPERATURE > temp_threshold:
        LOGGER.info("Emitting high temperature event: {}".format(GLOBAL_TEMPERATURE))
        exp_thing.emit_event(NAME_EVENT_TEMP_HIGH, GLOBAL_TEMPERATURE)


async def temp_read_handler():
    """Custom handler for the 'Temperature' property."""

    LOGGER.info("Doing some work to simulate temperature retrieval")
    await asyncio.sleep(random.random() * 3.0)

    return GLOBAL_TEMPERATURE


async def main():
    update_temp()

    LOGGER.info("Creating WebSocket server on: {}".format(WEBSOCKET_PORT))

    ws_server = WebsocketServer(port=WEBSOCKET_PORT)

    LOGGER.info("Creating HTTP server on: {}".format(HTTP_PORT))

    http_server = HTTPServer(port=HTTP_PORT)

    LOGGER.info("Creating servient with TD catalogue on: {}".format(CATALOGUE_PORT))

    servient = Servient(catalogue_port=CATALOGUE_PORT)
    servient.add_server(ws_server)
    servient.add_server(http_server)

    LOGGER.info("Starting servient")

    wot = await servient.start()

    LOGGER.info("Exposing and configuring Thing")

    exposed_thing = wot.produce(json.dumps(DESCRIPTION))
    exposed_thing.set_property_read_handler(NAME_PROP_TEMP, temp_read_handler)
    await exposed_thing.properties[NAME_PROP_TEMP_THRESHOLD].write(DEFAULT_TEMP_THRESHOLD)
    exposed_thing.expose()

    async def run_periodic_update():
        while True:
            await asyncio.sleep(PERIODIC_MS / 1000)
            update_temp()

    async def run_periodic_emit():
        while True:
            await asyncio.sleep(PERIODIC_MS / 1000)
            await emit_temp_high(exposed_thing)

    asyncio.create_task(run_periodic_update())
    asyncio.create_task(run_periodic_emit())

    await asyncio.Future()


def _setup_logging() -> None:
    colors = {
        logging.DEBUG: "\033[37m",
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    reset = "\033[0m"

    class _ColorFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            record.levelname = f"{colors.get(record.levelno, '')}{record.levelname}{reset}"
            return super().format(record)

    handler = logging.StreamHandler()
    handler.setFormatter(_ColorFormatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logging.root.setLevel(logging.INFO)
    logging.root.addHandler(handler)


if __name__ == "__main__":
    _setup_logging()
    asyncio.run(main())
