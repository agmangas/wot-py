#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import uuid

import pytest
import tornado.gen
from faker import Faker

from wotpy.protocols.http.server import HTTPServer
from wotpy.td.thing import Thing
from wotpy.wot.dictionaries.interaction import PropertyInitDict, ActionInitDict, EventInitDict
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient


@pytest.fixture
def http_server():
    """Builds an HTTPServer instance that contains an ExposedThing."""

    exposed_thing = ExposedThing(servient=Servient(), thing=Thing(id=uuid.uuid4().urn))

    exposed_thing.add_property(uuid.uuid4().hex, PropertyInitDict({
        "type": "number",
        "value": Faker().pyint(),
        "writable": True,
        "observable": True
    }))

    exposed_thing.add_property(uuid.uuid4().hex, PropertyInitDict({
        "type": "number",
        "value": Faker().pyint(),
        "writable": True,
        "observable": True
    }))

    exposed_thing.add_event(uuid.uuid4().hex, EventInitDict({
        "type": "object"
    }))

    action_name = uuid.uuid4().hex

    exposed_thing.add_action(action_name, ActionInitDict({
        "input": {"type": "number"},
        "output": {"type": "number"}
    }))

    @tornado.gen.coroutine
    def triple(parameters):
        input_value = parameters.get("input")
        yield tornado.gen.sleep(0)
        raise tornado.gen.Return(input_value * 3)

    exposed_thing.set_action_handler(action_name, triple)

    port = random.randint(20000, 40000)

    server = HTTPServer(port=port)
    server.add_exposed_thing(exposed_thing)
    server.start()

    return server
