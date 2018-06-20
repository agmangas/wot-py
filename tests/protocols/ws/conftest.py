#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import re
import time
import uuid

# noinspection PyPackageRequirements
import pytest
import tornado.gen
import tornado.ioloop
import tornado.testing
import tornado.websocket
# noinspection PyPackageRequirements
from faker import Faker
from six.moves.urllib.parse import urlparse, urlunparse

from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.thing import Thing
from wotpy.wot.dictionaries.interaction import PropertyInitDict, ActionInitDict, EventInitDict
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient


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

    prop_init_01 = PropertyInitDict({
        "type": "string",
        "value": Faker().sentence(),
        "writable": True,
        "observable": True
    })

    prop_init_02 = PropertyInitDict({
        "type": "string",
        "value": Faker().sentence(),
        "writable": True,
        "observable": True
    })

    prop_init_03 = PropertyInitDict({
        "type": "string",
        "value": Faker().sentence(),
        "writable": True,
        "observable": True
    })

    event_init_01 = EventInitDict({
        "type": "object"
    })

    action_init_01 = ActionInitDict({
        "input": {"type": "string"},
        "output": {"type": "string"}
    })

    def async_lower(parameters):
        loop = tornado.ioloop.IOLoop.current()
        input_value = parameters.get("input")
        return loop.run_in_executor(None, lambda x: time.sleep(0.1) or x.lower(), input_value)

    exposed_thing_01.add_property(prop_name_01, prop_init_01)
    exposed_thing_01.add_property(prop_name_02, prop_init_02)
    exposed_thing_01.add_event(event_name_01, event_init_01)
    exposed_thing_01.add_action(action_name_01, action_init_01)
    exposed_thing_01.set_action_handler(action_name_01, async_lower)

    exposed_thing_02.add_property(prop_name_03, prop_init_03)

    ws_port = random.randint(20000, 40000)

    ws_server = WebsocketServer(port=ws_port)
    ws_server.add_exposed_thing(exposed_thing_01)
    ws_server.add_exposed_thing(exposed_thing_02)
    ws_server.start()

    url_thing_01 = build_websocket_url(exposed_thing_01, ws_server, ws_port)
    url_thing_02 = build_websocket_url(exposed_thing_02, ws_server, ws_port)

    return {
        "exposed_thing_01": exposed_thing_01,
        "exposed_thing_02": exposed_thing_02,
        "prop_name_01": prop_name_01,
        "prop_init_01": prop_init_01,
        "prop_name_02": prop_name_02,
        "prop_init_02": prop_init_02,
        "prop_name_03": prop_name_03,
        "prop_init_03": prop_init_03,
        "event_name_01": event_name_01,
        "event_init_01": event_init_01,
        "action_name_01": action_name_01,
        "action_init_01": action_init_01,
        "ws_server": ws_server,
        "url_thing_01": url_thing_01,
        "url_thing_02": url_thing_02,
        "ws_port": ws_port
    }
