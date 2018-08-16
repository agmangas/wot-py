#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import uuid

import pytest
import tornado.gen
from faker import Faker

from wotpy.protocols.http.server import HTTPServer
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
    server.start()

    return server
