#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import uuid

import pytest
import tornado.gen
import tornado.ioloop
from faker import Faker

from wotpy.protocols.support import is_mqtt_supported
from wotpy.td.thing import Thing
from wotpy.wot.dictionaries.interaction import ActionFragment, EventFragment, PropertyFragment
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient

collect_ignore = []

if not is_mqtt_supported():
    logging.warning("Skipping MQTT tests due to unsupported platform")
    collect_ignore += ["test_server.py"]


@pytest.fixture
def mqtt_server():
    """Builds a MQTTServer instance that contains an ExposedThing."""

    from wotpy.protocols.mqtt.server import MQTTServer

    exposed_thing = ExposedThing(servient=Servient(), thing=Thing(id=uuid.uuid4().urn))

    exposed_thing.add_property(uuid.uuid4().hex, PropertyFragment({
        "type": "string",
        "writable": True,
        "observable": True
    }), value=Faker().pyint())

    exposed_thing.add_event(uuid.uuid4().hex, EventFragment({
        "type": "number"
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

    # ToDo: Set broker URL
    server = MQTTServer(broker_url=None)
    server.add_exposed_thing(exposed_thing)

    @tornado.gen.coroutine
    def start():
        yield server.start()

    tornado.ioloop.IOLoop.current().add_callback(start)

    return server
