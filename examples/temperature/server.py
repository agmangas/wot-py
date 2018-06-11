#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple Temperature Thing that serves as an
example for how to use the WotPy servient.
"""

import json
import logging
import random

import tornado.gen
from tornado.ioloop import IOLoop, PeriodicCallback

from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

CATALOGUE_PORT = 9292
WEBSOCKET_PORT = 9393

GLOBAL_TEMPERATURE = None
PERIODIC_MS = 3000
DEFAULT_TEMP_THRESHOLD = 27.0

logging.basicConfig()
LOGGER = logging.getLogger("temperature-server")
LOGGER.setLevel(logging.INFO)

NAME_THING = "urn:temperaturething"
NAME_PROP_TEMP = "temperature"
NAME_PROP_TEMP_THRESHOLD = "high-temperature-threshold"
NAME_EVENT_TEMP_HIGH = "high-temperature"

DESCRIPTION = {
    "id": NAME_THING,
    "properties": {
        NAME_PROP_TEMP: {
            "type": "number",
            "writable": False,
            "observable": True
        },
        NAME_PROP_TEMP_THRESHOLD: {
            "type": "number",
            "writable": True,
            "observable": True
        }
    },
    "events": {
        NAME_EVENT_TEMP_HIGH: {
            "type": "number"
        }
    }
}


def update_temp():
    """Updates the global temperature value."""

    global GLOBAL_TEMPERATURE
    GLOBAL_TEMPERATURE = round(random.randint(20.0, 30.0) + random.random(), 2)
    LOGGER.info("Current temperature: {}".format(GLOBAL_TEMPERATURE))


@tornado.gen.coroutine
def emit_temp_high(exp_thing):
    """Emits a 'Temperature High' event if the temperature is over the threshold."""

    temp_threshold = yield exp_thing.read_property(NAME_PROP_TEMP_THRESHOLD)

    if temp_threshold and GLOBAL_TEMPERATURE > temp_threshold:
        LOGGER.info("Emitting high temperature event: {}".format(GLOBAL_TEMPERATURE))
        exp_thing.emit_event(NAME_EVENT_TEMP_HIGH, GLOBAL_TEMPERATURE)


@tornado.gen.coroutine
def temp_read_handler(property_name):
    """Custom handler for the 'Temperature' property."""

    assert property_name == NAME_PROP_TEMP

    LOGGER.info("Doing some work to simulate temperature retrieval")
    yield tornado.gen.sleep(random.random() * 3.0)

    raise tornado.gen.Return(GLOBAL_TEMPERATURE)


if __name__ == "__main__":
    update_temp()

    LOGGER.info("Creating WebSocket server on: {}".format(WEBSOCKET_PORT))

    ws_server = WebsocketServer(port=WEBSOCKET_PORT)

    LOGGER.info("Creating servient with TD catalogue on: {}".format(CATALOGUE_PORT))

    servient = Servient()
    servient.add_server(ws_server)
    servient.enable_td_catalogue(CATALOGUE_PORT)

    LOGGER.info("Starting servient")

    wot = servient.start()

    LOGGER.info("Exposing and configuring Thing")

    exposed_thing = wot.produce(json.dumps(DESCRIPTION))
    exposed_thing.set_property_read_handler(read_handler=temp_read_handler, property_name=NAME_PROP_TEMP)
    exposed_thing.write_property(NAME_PROP_TEMP_THRESHOLD, DEFAULT_TEMP_THRESHOLD)
    exposed_thing.start()

    periodic_update = PeriodicCallback(update_temp, PERIODIC_MS)
    periodic_update.start()


    @tornado.gen.coroutine
    def emit_for_exposed_thing():
        yield emit_temp_high(exposed_thing)


    periodic_emit = PeriodicCallback(emit_for_exposed_thing, PERIODIC_MS)
    periodic_emit.start()

    LOGGER.info("Starting loop")

    IOLoop.current().start()
