#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple Temperature Thing that serves as an
example for how to use the WotPy servient.
"""

import json
import logging
import multiprocessing
import random
import time

# noinspection PyCompatibility
from concurrent.futures import ThreadPoolExecutor
from tornado.ioloop import IOLoop, PeriodicCallback

from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.constants import WOT_TD_CONTEXT_URL
from wotpy.td.enums import InteractionTypes
from wotpy.wot.servient import Servient

CATALOGUE_PORT = 9292
WEBSOCKET_PORT = 9393

GLOBAL_TEMPERATURE = None
PERIODIC_MS = 3000
DEFAULT_TEMP_THRESHOLD = 27.0

logging.basicConfig()
LOGGER = logging.getLogger("temp-servient")
LOGGER.setLevel(logging.INFO)

max_workers = multiprocessing.cpu_count() * 2
EXECUTOR = ThreadPoolExecutor(max_workers=max_workers)

NAME_THING = "TemperatureThing"
NAME_PROP_TEMP = "temperature"
NAME_PROP_TEMP_THRESHOLD = "high-temperature-threshold"
NAME_EVENT_TEMP_HIGH = "high-temperature"

DESCRIPTION = {
    "@context": [WOT_TD_CONTEXT_URL],
    "name": NAME_THING,
    "interaction": [{
        "@type": [InteractionTypes.PROPERTY],
        "name": NAME_PROP_TEMP,
        "outputData": {"type": "number"},
        "writable": False,
        "observable": True,
    }, {
        "@type": [InteractionTypes.PROPERTY],
        "name": NAME_PROP_TEMP_THRESHOLD,
        "outputData": {"type": "number"},
        "writable": True,
        "observable": True
    }, {
        "@type": [InteractionTypes.EVENT],
        "name": NAME_EVENT_TEMP_HIGH,
        "outputData": {"type": "number"}
    }]
}


def update_temp():
    """Updates the global temperature value."""

    global GLOBAL_TEMPERATURE
    GLOBAL_TEMPERATURE = round(random.randint(20.0, 30.0) + random.random(), 2)
    LOGGER.info("Current temperature: {}".format(GLOBAL_TEMPERATURE))


def emit_temp_high(exp_thing):
    """Emits a 'Temperature High' event if the temperature is over the threshold."""

    temp_threshold = exp_thing.read_property(NAME_PROP_TEMP_THRESHOLD).result()

    if temp_threshold and GLOBAL_TEMPERATURE > temp_threshold:
        LOGGER.info("Emitting high temperature event: {}".format(GLOBAL_TEMPERATURE))
        exp_thing.emit_event(NAME_EVENT_TEMP_HIGH, GLOBAL_TEMPERATURE)


def temp_read_handler(property_name):
    """Custom handler for the 'Temperature' property."""

    assert property_name == NAME_PROP_TEMP

    def sleep_and_get_temp():
        """Wait for a while and return a random temperature."""

        LOGGER.info("Doing some work to simulate temperature retrieval")
        time.sleep(random.random() * 3.0)
        return GLOBAL_TEMPERATURE

    return EXECUTOR.submit(sleep_and_get_temp)


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

    periodic_emit = PeriodicCallback(lambda: emit_temp_high(exposed_thing), PERIODIC_MS)
    periodic_emit.start()

    LOGGER.info("Starting loop")

    IOLoop.current().start()
