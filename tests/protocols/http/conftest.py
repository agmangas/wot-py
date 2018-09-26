#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import uuid

import pytest
import tornado.gen
import tornado.ioloop
from faker import Faker

from wotpy.protocols.http.server import HTTPServer
from wotpy.td.description import ThingDescription
from wotpy.td.thing import Thing
from wotpy.wot.dictionaries.interaction import PropertyFragment, ActionFragment, EventFragment
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient


@pytest.fixture
def http_server():
    """Builds an HTTPServer instance that contains an ExposedThing."""

    exposed_thing = ExposedThing(servient=Servient(), thing=Thing(id=uuid.uuid4().urn))

    exposed_thing.add_property(uuid.uuid4().hex, PropertyFragment({
        "type": "number",
        "writable": True,
        "observable": True
    }), value=Faker().pyint())

    exposed_thing.add_property(uuid.uuid4().hex, PropertyFragment({
        "type": "number",
        "writable": True,
        "observable": True
    }), value=Faker().pyint())

    exposed_thing.add_event(uuid.uuid4().hex, EventFragment({
        "type": "object"
    }))

    action_name = uuid.uuid4().hex

    @tornado.gen.coroutine
    def triple(parameters):
        input_value = parameters.get("input")
        yield tornado.gen.sleep(0)
        raise tornado.gen.Return(input_value * 3)

    exposed_thing.add_action(action_name, ActionFragment({
        "input": {"type": "number"},
        "output": {"type": "number"}
    }), triple)

    port = random.randint(20000, 40000)

    server = HTTPServer(port=port)
    server.add_exposed_thing(exposed_thing)

    @tornado.gen.coroutine
    def start():
        yield server.start()

    tornado.ioloop.IOLoop.current().run_sync(start)

    return server


@pytest.fixture
def http_servient():
    """Returns a Servient that exposes an HTTP server and one ExposedThing."""

    http_port = random.randint(20000, 40000)
    http_server = HTTPServer(port=http_port)

    servient = Servient()
    servient.add_server(http_server)

    wot = servient.start()

    property_name_01 = uuid.uuid4().hex
    property_name_02 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex

    td_dict = {
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
                    "type": "number"
                },
                "output": {
                    "type": "number"
                },
            }
        },
        "events": {
            event_name_01: {
                "type": "string"
            }
        },
    }

    td = ThingDescription(td_dict)

    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    @tornado.gen.coroutine
    def action_handler(parameters):
        input_value = parameters.get("input")
        raise tornado.gen.Return(int(input_value) * 2)

    exposed_thing.set_action_handler(action_name_01, action_handler)

    return servient
