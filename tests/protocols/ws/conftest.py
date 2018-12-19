#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import time
import uuid

# noinspection PyPackageRequirements
import pytest
import tornado.concurrent
import tornado.gen
import tornado.gen
import tornado.ioloop
import tornado.ioloop
import tornado.testing
import tornado.websocket
import tornado.websocket
# noinspection PyPackageRequirements
from faker import Faker
from six.moves.urllib.parse import urlparse, urlunparse

from tests.utils import find_free_port
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.dictionaries.interaction import PropertyFragmentDict, ActionFragmentDict, EventFragmentDict
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing


def build_websocket_url(exposed_thing, ws_server, server_port):
    """Returns the WS connection URL for the given ExposedThing."""

    base_url = ws_server.build_base_url(hostname="localhost", thing=exposed_thing.thing)
    parsed_url = urlparse(base_url)
    test_netloc = re.sub(r':(\d+)$', ':{}'.format(server_port), parsed_url.netloc)

    test_url_parts = list(parsed_url)
    test_url_parts[1] = test_netloc

    return urlunparse(test_url_parts)


@pytest.fixture
def websocket_server():
    """Builds a WebsocketServer instance with some ExposedThings."""

    servient = Servient()

    thing_01_id = uuid.uuid4().urn
    thing_02_id = uuid.uuid4().urn

    exposed_thing_01 = ExposedThing(servient=servient, thing=Thing(id=thing_01_id))
    exposed_thing_02 = ExposedThing(servient=servient, thing=Thing(id=thing_02_id))

    prop_name_01 = uuid.uuid4().hex
    prop_name_02 = uuid.uuid4().hex
    prop_name_03 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex

    prop_value_01 = Faker().sentence()
    prop_value_02 = Faker().sentence()
    prop_value_03 = Faker().sentence()

    prop_init_01 = PropertyFragmentDict({
        "type": "string",
        "observable": True
    })

    prop_init_02 = PropertyFragmentDict({
        "type": "string",
        "observable": True
    })

    prop_init_03 = PropertyFragmentDict({
        "type": "string",
        "observable": True
    })

    event_init_01 = EventFragmentDict({
        "type": "object"
    })

    action_init_01 = ActionFragmentDict({
        "input": {"type": "string"},
        "output": {"type": "string"}
    })

    def async_lower(parameters):
        loop = tornado.ioloop.IOLoop.current()
        input_value = parameters.get("input")
        return loop.run_in_executor(None, lambda x: time.sleep(0.1) or x.lower(), input_value)

    exposed_thing_01.add_property(prop_name_01, prop_init_01, value=prop_value_01)
    exposed_thing_01.add_property(prop_name_02, prop_init_02, value=prop_value_02)
    exposed_thing_01.add_event(event_name_01, event_init_01)
    exposed_thing_01.add_action(action_name_01, action_init_01, async_lower)

    exposed_thing_02.add_property(prop_name_03, prop_init_03, value=prop_value_03)

    ws_port = find_free_port()

    ws_server = WebsocketServer(port=ws_port)
    ws_server.add_exposed_thing(exposed_thing_01)
    ws_server.add_exposed_thing(exposed_thing_02)

    @tornado.gen.coroutine
    def start():
        yield ws_server.start()

    tornado.ioloop.IOLoop.current().run_sync(start)

    url_thing_01 = build_websocket_url(exposed_thing_01, ws_server, ws_port)
    url_thing_02 = build_websocket_url(exposed_thing_02, ws_server, ws_port)

    yield {
        "exposed_thing_01": exposed_thing_01,
        "exposed_thing_02": exposed_thing_02,
        "prop_name_01": prop_name_01,
        "prop_init_01": prop_init_01,
        "prop_value_01": prop_value_01,
        "prop_name_02": prop_name_02,
        "prop_init_02": prop_init_02,
        "prop_value_02": prop_value_02,
        "prop_name_03": prop_name_03,
        "prop_init_03": prop_init_03,
        "prop_value_03": prop_value_03,
        "event_name_01": event_name_01,
        "event_init_01": event_init_01,
        "action_name_01": action_name_01,
        "action_init_01": action_init_01,
        "ws_server": ws_server,
        "url_thing_01": url_thing_01,
        "url_thing_02": url_thing_02,
        "ws_port": ws_port
    }

    @tornado.gen.coroutine
    def stop():
        yield ws_server.stop()

    tornado.ioloop.IOLoop.current().run_sync(stop)


@pytest.fixture
def websocket_servient():
    """Returns a Servient that exposes a Websockets server and one ExposedThing."""

    ws_port = find_free_port()
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient(catalogue_port=None)
    servient.add_server(ws_server)

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
    }

    td = ThingDescription(td_dict)

    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    @tornado.gen.coroutine
    def action_handler(parameters):
        input_value = parameters.get("input")
        arg_b = input_value.get("arg_b") or uuid.uuid4().hex
        raise tornado.gen.Return(input_value.get("arg_a") + arg_b)

    exposed_thing.set_action_handler(action_name_01, action_handler)

    yield servient

    @tornado.gen.coroutine
    def shutdown():
        yield servient.shutdown()

    tornado.ioloop.IOLoop.current().run_sync(shutdown)
