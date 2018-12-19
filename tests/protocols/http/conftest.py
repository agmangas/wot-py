#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import pytest
import tornado.gen
import tornado.ioloop
from faker import Faker

from tests.utils import find_free_port
from wotpy.protocols.http.server import HTTPServer
from wotpy.wot.dictionaries.interaction import PropertyFragmentDict, ActionFragmentDict, EventFragmentDict
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing


@pytest.fixture
def http_server():
    """Builds an HTTPServer instance that contains an ExposedThing."""

    exposed_thing = ExposedThing(servient=Servient(), thing=Thing(id=uuid.uuid4().urn))

    exposed_thing.add_property(uuid.uuid4().hex, PropertyFragmentDict({
        "type": "number",
        "observable": True
    }), value=Faker().pyint())

    exposed_thing.add_property(uuid.uuid4().hex, PropertyFragmentDict({
        "type": "number",
        "observable": True
    }), value=Faker().pyint())

    exposed_thing.add_event(uuid.uuid4().hex, EventFragmentDict({
        "type": "object"
    }))

    action_name = uuid.uuid4().hex

    @tornado.gen.coroutine
    def triple(parameters):
        input_value = parameters.get("input")
        yield tornado.gen.sleep(0)
        raise tornado.gen.Return(input_value * 3)

    exposed_thing.add_action(action_name, ActionFragmentDict({
        "input": {"type": "number"},
        "output": {"type": "number"}
    }), triple)

    port = find_free_port()

    server = HTTPServer(port=port)
    server.add_exposed_thing(exposed_thing)

    @tornado.gen.coroutine
    def start():
        yield server.start()

    tornado.ioloop.IOLoop.current().run_sync(start)

    yield server

    @tornado.gen.coroutine
    def stop():
        yield server.stop()

    tornado.ioloop.IOLoop.current().run_sync(stop)


@pytest.fixture
def http_servient():
    """Returns a Servient that exposes an HTTP server and one ExposedThing."""

    http_port = find_free_port()
    http_server = HTTPServer(port=http_port)

    servient = Servient(catalogue_port=None)
    servient.add_server(http_server)

    @tornado.gen.coroutine
    def start():
        raise tornado.gen.Return((yield servient.start()))

    wot = tornado.ioloop.IOLoop.current().run_sync(start)

    property_name_01 = uuid.uuid4().hex
    property_name_02 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex

    td_dict = {
        "id": uuid.uuid4().urn,
        "name": uuid.uuid4().hex,
        "properties": {
            property_name_01: {
                "observable": True,
                "type": "string"
            },
            property_name_02: {
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

    yield servient

    @tornado.gen.coroutine
    def shutdown():
        yield servient.shutdown()

    tornado.ioloop.IOLoop.current().run_sync(shutdown)
