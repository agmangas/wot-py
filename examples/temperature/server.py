#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from tornado.ioloop import IOLoop, PeriodicCallback

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

CATALOGUE_PORT = 9090
WEBSOCKET_PORT = 9393
HTTP_PORT = 9494

GLOBAL_TEMPERATURE = None
PERIODIC_MS = 3000
DEFAULT_TEMP_THRESHOLD = 27.0

logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

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

    periodic_update = PeriodicCallback(update_temp, PERIODIC_MS)
    periodic_update.start()

    async def emit_for_exposed_thing():
        await emit_temp_high(exposed_thing)

    periodic_emit = PeriodicCallback(emit_for_exposed_thing, PERIODIC_MS)
    periodic_emit.start()


if __name__ == "__main__":
    LOGGER.info("Starting loop")
    IOLoop.current().add_callback(main)
    IOLoop.current().start()
