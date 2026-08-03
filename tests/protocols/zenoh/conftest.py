#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import random
import uuid

import pytest_asyncio
from faker import Faker

from tests.protocols.zenoh.router import get_test_router_url
from wotpy.protocols.zenoh.server import ZenohServer
from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1
from wotpy.wot.dictionaries.interaction import ActionFragmentDict, EventFragmentDict, PropertyFragmentDict
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing

collect_ignore = []


@pytest_asyncio.fixture(params=[{"property_callback_ms": None}])
async def zenoh_server(request):
    """Builds a ZenohServer instance that contains an ExposedThing."""

    router_url = get_test_router_url()
    server = ZenohServer(router_url=router_url, **request.param)
    servient_id = server.servient_id

    thing_name = uuid.uuid4().hex
    thing_fragment = ThingFragment({
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": uuid.uuid4().urn,
        "title": thing_name,
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc"
    })
    thing = Thing(thing_fragment=thing_fragment)
    exposed_thing = ExposedThing(servient=Servient(), thing=thing)

    prop_name = uuid.uuid4().hex
    exposed_thing.add_property(prop_name, PropertyFragmentDict({
        "type": "string",
        "observable": True
    }), value=Faker().sentence())

    event_name = uuid.uuid4().hex
    exposed_thing.add_event(event_name, EventFragmentDict({
        "type": "number"
    }))

    action_name = uuid.uuid4().hex

    async def handler(parameters):
        input_value = parameters.get("input")
        await asyncio.sleep(random.random() * 0.1)
        return "{:f}".format(input_value)

    exposed_thing.add_action(action_name, ActionFragmentDict({
        "input": {"type": "number"},
        "output": {"type": "string"}
    }), handler)

    server.add_exposed_thing(exposed_thing)

    wot = await server.start()

    yield server

    await server.stop()


@pytest_asyncio.fixture
async def zenoh_servient():
    """Returns a Servient that exposes a Zenoh server and one ExposedThing."""

    router_url = get_test_router_url()
    server = ZenohServer(router_url=router_url)
    servient_id = server.servient_id

    servient = Servient(catalogue_port=None)
    servient.add_server(server)

    wot = await servient.start()

    property_name_01 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex

    thing_name = uuid.uuid4().hex
    td_dict = {
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": uuid.uuid4().urn,
        "title": thing_name,
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
            }
        },
        "actions": {
            action_name_01: {
                "input": {
                    "type": "number"
                },
                "output": {
                    "type": "number"
                }
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

    async def action_handler(parameters):
        input_value = parameters.get("input")
        return int(input_value) * 2

    exposed_thing.set_action_handler(action_name_01, action_handler)

    yield servient

    await servient.shutdown()
