#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import uuid

# noinspection PyPackageRequirements
import pytest
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.websocket

from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.description import ThingDescription
from wotpy.wot.servient import Servient


@pytest.fixture
def websocket_servient():
    """Builds, starts and returns an ExposedThing and the Servient that contains it."""

    ws_port = random.randint(20000, 40000)
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient()
    servient.add_server(ws_server)

    wot = servient.start()

    property_name_01 = uuid.uuid4().hex
    property_name_02 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex

    td = ThingDescription(doc={
        "id": uuid.uuid4().urn,
        "name": uuid.uuid4().hex,
        "properties": {
            property_name_01: {
                "writable": True,
                "observable": True,
                "type": "string"
            },
            property_name_02: {
                "writable": True,
                "observable": True,
                "type": "string"
            }
        },
        "actions": {
            action_name_01: {
                "input": {
                    "type": "object"
                },
                "output": {
                    "type": "string"
                },
            }
        },
        "events": {
            event_name_01: {
                "type": "string"
            }
        },
    })

    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    @tornado.gen.coroutine
    def action_handler(parameters):
        input_value = parameters.get("input")
        arg_b = input_value.get("arg_b") or uuid.uuid4().hex
        raise tornado.gen.Return(input_value.get("arg_a") + arg_b)

    exposed_thing.set_action_handler(action_name_01, action_handler)

    return {
        "servient": servient,
        "exposed_thing": exposed_thing
    }
