#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

import asyncio
import re
import time
import uuid
from urllib.parse import urlparse, urlunparse

import pytest_asyncio
import tornado.websocket
from faker import Faker

from tests.utils import find_free_port
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1
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


@pytest_asyncio.fixture
async def websocket_server():
    """Builds a WebsocketServer instance with some ExposedThings."""

    ws_port = find_free_port()

    servient = Servient()

    thing_01_id = uuid.uuid4().urn
    thing_01_title = uuid.uuid4().hex
    thing_02_id = uuid.uuid4().urn
    thing_02_title = uuid.uuid4().hex

    td_json = {
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc"
    }

    thing_01_json = dict(td_json)
    thing_01_json["title"] = thing_01_title
    thing_01_json["id"] = thing_01_id
    thing_01 = ThingDescription(doc=thing_01_json).build_thing()
    exposed_thing_01 = ExposedThing(servient=Servient(), thing=thing_01)

    thing_02_json = dict(td_json)
    thing_02_json["title"] = thing_02_title
    thing_02_json["id"] = thing_02_id
    thing_02 = ThingDescription(doc=thing_02_json).build_thing()
    exposed_thing_02 = ExposedThing(servient=Servient(), thing=thing_02)

    prop_name_01 = uuid.uuid4().hex
    prop_name_02 = uuid.uuid4().hex
    prop_name_03 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex

    prop_value_01 = Faker().sentence()
    prop_value_02 = Faker().sentence()
    prop_value_03 = Faker().sentence()

    prop_init_01 = PropertyFragmentDict({"type": "string", "observable": True})

    prop_init_02 = PropertyFragmentDict({"type": "string", "observable": True})

    prop_init_03 = PropertyFragmentDict({"type": "string", "observable": True})

    event_init_01 = EventFragmentDict({"type": "object"})

    action_init_01 = ActionFragmentDict(
        {"input": {"type": "string"}, "output": {"type": "string"}}
    )

    def async_lower(parameters):
        loop = asyncio.get_running_loop()
        input_value = parameters.get("input")
        return loop.run_in_executor(
            None, lambda x: time.sleep(0.1) or x.lower(), input_value
        )

    exposed_thing_01.add_property(prop_name_01, prop_init_01, value=prop_value_01)
    exposed_thing_01.add_property(prop_name_02, prop_init_02, value=prop_value_02)
    exposed_thing_01.add_event(event_name_01, event_init_01)
    exposed_thing_01.add_action(action_name_01, action_init_01, async_lower)

    exposed_thing_02.add_property(prop_name_03, prop_init_03, value=prop_value_03)

    ws_server = WebsocketServer(port=ws_port)
    ws_server.add_exposed_thing(exposed_thing_01)
    ws_server.add_exposed_thing(exposed_thing_02)

    wot = await ws_server.start()

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

    await ws_server.stop()


@pytest_asyncio.fixture
async def websocket_servient():
    """Returns a Servient that exposes a Websockets server and one ExposedThing."""

    ws_port = find_free_port()
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient(catalogue_port=None)
    servient.add_server(ws_server)

    wot = await servient.start()

    property_name_01 = uuid.uuid4().hex
    property_name_02 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex

    title = uuid.uuid4().hex
    td_dict = {
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": uuid.uuid4().urn,
        "title": title,
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc",
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
                }
            }
        },
        "events": {
            event_name_01: {
                "type": "string"
            }
        }
    }

    td = ThingDescription(td_dict)

    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    async def action_handler(parameters):
        input_value = parameters.get("input")
        arg_b = input_value.get("arg_b") or uuid.uuid4().hex
        return(input_value.get("arg_a") + arg_b)

    exposed_thing.set_action_handler(action_name_01, action_handler)

    yield servient

    await servient.shutdown()
