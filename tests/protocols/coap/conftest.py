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

import logging
import uuid

import pytest_asyncio
from faker import Faker

from tests.utils import find_free_port
from wotpy.support import is_coap_supported
from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1
from wotpy.wot.dictionaries.interaction import PropertyFragmentDict, EventFragmentDict, ActionFragmentDict
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing

collect_ignore = []

if not is_coap_supported():
    logging.warning("Skipping CoAP tests due to unsupported platform")
    collect_ignore += ["test_server.py", "test_client.py"]



@pytest_asyncio.fixture
async def coap_server():
    """Builds a CoAPServer instance that contains an ExposedThing."""

    from wotpy.protocols.coap.server import CoAPServer

    port = find_free_port()

    thing_fragment = ThingFragment({
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": uuid.uuid4().urn,
        "title": uuid.uuid4().hex,
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc"
    })
    thing = Thing(thing_fragment=thing_fragment)
    exposed_thing = ExposedThing(servient=Servient(), thing=thing)

    property_name_01 = uuid.uuid4().hex
    exposed_thing.add_property(
        property_name_01, 
        PropertyFragmentDict({"type": "number", "observable": True}),
        value=Faker().pyint()
    )

    property_name_02 = uuid.uuid4().hex
    exposed_thing.add_property(
        property_name_02,
        PropertyFragmentDict({"type": "string", "observable": True}),
        value=Faker().pyint()
    )

    event_name = uuid.uuid4().hex
    exposed_thing.add_event(event_name, EventFragmentDict({"type": "object"}))

    action_name = uuid.uuid4().hex

    async def triple(input_value):
        return input_value * 3

    exposed_thing.add_action(
        action_name,
        ActionFragmentDict({"input": {"type": "number"}, "output": {"type": "number"}}),
        triple
    )


    server = CoAPServer(port=port)
    server.add_exposed_thing(exposed_thing)

    wot = await server.start()

    yield server

    await server.stop()


@pytest_asyncio.fixture
async def coap_servient():
    """Returns a Servient that exposes a CoAP server and one ExposedThing."""

    from wotpy.protocols.coap.server import CoAPServer

    coap_port = find_free_port()
    the_coap_server = CoAPServer(port=coap_port)
    servient = Servient(catalogue_port=None)
    servient.add_server(the_coap_server)
    wot = await servient.start()

    property_name = uuid.uuid4().hex
    action_name = uuid.uuid4().hex
    event_name = uuid.uuid4().hex

    td_dict = {
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": uuid.uuid4().urn,
        "title": uuid.uuid4().hex,
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc",
        "properties": {
            property_name: {
                "observable": True,
                "type": "string"
            }
        },
        "actions": {
            action_name: {
                "input": {
                    "type": "number"
                },
                "output": {
                    "type": "number"
                }
            }
        },
        "events": {
            event_name: {
                "type": "string"
            }
        }
    }

    td = ThingDescription(td_dict)
    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    async def action_handler(input_value):
        return int(input_value) * 2

    exposed_thing.set_action_handler(action_name, action_handler)
    yield servient
    await servient.shutdown()
