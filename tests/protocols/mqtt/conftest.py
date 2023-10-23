#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import random
import uuid

import pytest
import tornado.gen
import tornado.ioloop
from faker import Faker

from wotpy.support import is_mqtt_supported
from wotpy.wot.dictionaries.interaction import (
    ActionFragmentDict,
    EventFragmentDict,
    PropertyFragmentDict,
)
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing

collect_ignore = []

skip_reasons = [(not is_mqtt_supported(), "Unsupported platform")]

for skip_check, reason in skip_reasons:
    if skip_check:
        logging.warning("Skipping MQTT tests: {}".format(reason))
        collect_ignore += ["test_server.py", "test_client.py"]
        break


@pytest.fixture(params=[{"property_callback_ms": None}])
def mqtt_server(request):
    """Builds a MQTTServer instance that contains an ExposedThing."""

    from tests.protocols.mqtt.broker import get_test_broker_url
    from wotpy.protocols.mqtt.server import MQTTServer

    exposed_thing = ExposedThing(servient=Servient(), thing=Thing(id=uuid.uuid4().urn))

    exposed_thing.add_property(
        uuid.uuid4().hex,
        PropertyFragmentDict({"type": "string", "observable": True}),
        value=Faker().sentence(),
    )

    exposed_thing.add_event(uuid.uuid4().hex, EventFragmentDict({"type": "number"}))

    action_name = uuid.uuid4().hex

    @tornado.gen.coroutine
    def handler(parameters):
        input_value = parameters.get("input")
        yield tornado.gen.sleep(random.random() * 0.1)
        raise tornado.gen.Return("{:f}".format(input_value))

    exposed_thing.add_action(
        action_name,
        ActionFragmentDict({"input": {"type": "number"}, "output": {"type": "string"}}),
        handler,
    )

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


@pytest.fixture
async def mqtt_servient():
    """Returns a Servient that exposes a CoAP server and one ExposedThing."""

    from tests.protocols.mqtt.broker import get_test_broker_url
    from wotpy.protocols.mqtt.server import MQTTServer

    server = MQTTServer(broker_url=get_test_broker_url())
    servient = Servient(catalogue_port=None)
    servient.add_server(server)
    wot = await servient.start()

    property_name_01 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex

    td_dict = {
        "id": uuid.uuid4().urn,
        "name": uuid.uuid4().hex,
        "properties": {property_name_01: {"observable": True, "type": "string"}},
        "actions": {
            action_name_01: {
                "input": {"type": "number"},
                "output": {"type": "number"},
            }
        },
        "events": {event_name_01: {"type": "string"}},
    }

    td = ThingDescription(td_dict)
    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    async def action_handler(parameters):
        input_value = parameters.get("input")
        return int(input_value) * 2

    exposed_thing.set_action_handler(action_name_01, action_handler)

    yield servient

    await servient.shutdown()
