#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
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


@pytest.fixture(params=[{"property_callback_ms": None}])
def mqtt_server(request):
    """Builds a MQTTServer instance that contains an ExposedThing."""

    from wotpy.protocols.mqtt.server import MQTTServer
    from tests.protocols.mqtt.broker import get_test_broker_url

    exposed_thing = ExposedThing(servient=Servient(), thing=Thing(id=uuid.uuid4().urn))

    exposed_thing.add_property(uuid.uuid4().hex, PropertyFragment({
        "type": "string",
        "writable": True,
        "observable": True
    }), value=Faker().sentence())

    exposed_thing.add_event(uuid.uuid4().hex, EventFragment({
        "type": "number"
    }))

    action_name = uuid.uuid4().hex

    @tornado.gen.coroutine
    def handler(parameters):
        input_value = parameters.get("input")
        yield tornado.gen.sleep(random.random() * 0.1)
        raise tornado.gen.Return("{:f}".format(input_value))

    exposed_thing.add_action(action_name, ActionFragment({
        "input": {"type": "number"},
        "output": {"type": "string"}
    }), handler)

    server = MQTTServer(broker_url=get_test_broker_url(), **request.param)
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
