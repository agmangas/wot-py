#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import uuid

import pytest
import tornado.gen
from faker import Faker

from wotpy.protocols.support import is_coap_supported
from wotpy.td.thing import Thing
from wotpy.wot.dictionaries.interaction import PropertyFragment, EventFragment, ActionFragment
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient

collect_ignore = []

if not is_coap_supported():
    logging.warning("Skipping CoAP tests due to unsupported platform")
    collect_ignore += ["test_server.py"]


@pytest.fixture(params=[{"action_clear_ms": 5000}])
def coap_server(request):
    """Builds a CoAPServer instance that contains an ExposedThing."""

    from wotpy.protocols.coap.server import CoAPServer

    exposed_thing = ExposedThing(servient=Servient(), thing=Thing(id=uuid.uuid4().urn))

    exposed_thing.add_property(uuid.uuid4().hex, PropertyFragment({
        "type": "number",
        "writable": True,
        "observable": True
    }), value=Faker().pyint())

    exposed_thing.add_property(uuid.uuid4().hex, PropertyFragment({
        "type": "string",
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
        raise tornado.gen.Return(input_value * 3)

    exposed_thing.add_action(action_name, ActionFragment({
        "input": {"type": "number"},
        "output": {"type": "number"}
    }), triple)

    port = random.randint(20000, 40000)

    server = CoAPServer(port=port, **request.param)
    server.add_exposed_thing(exposed_thing)
    server.start()

    return server
