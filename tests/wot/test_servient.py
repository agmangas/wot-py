#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 CTIC Centro Tecnologico
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

import json
import random
import uuid

import pytest
import tornado.httpclient
from faker import Faker

from tests.utils import find_free_port, run_test_coroutine
from wotpy.protocols.enums import Protocols
from wotpy.protocols.ws.client import WebsocketClient
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1
from wotpy.wot.consumed.thing import ConsumedThing
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.wot import WoT

TD_DICT_01 = {
    "@context": [
        WOT_TD_CONTEXT_URL_V1_1,
    ],
    "id": uuid.uuid4().urn,
    "title": Faker().sentence(),
    "securityDefinitions": {
        "nosec_sc":{
            "scheme":"nosec"
        }
    },
    "security": "nosec_sc",
    "properties": {
        "status": {
            "description": "Shows the current status of the lamp",
            "type": "string",
            "forms": [{
                "href": "coaps://mylamp.example.com:5683/status"
            }]
        }
    }
}

TD_DICT_02 = {
    "@context": [
        WOT_TD_CONTEXT_URL_V1_1,
    ],
    "id": uuid.uuid4().urn,
    "title": Faker().sentence(),
    "securityDefinitions": {
        "nosec_sc":{
            "scheme":"nosec"
        }
    },
    "security": "nosec_sc",
}


async def fetch_catalogue(servient, expanded=False):
    """Returns the TD catalogue exposed by the given Servient."""

    http_client = tornado.httpclient.AsyncHTTPClient()
    expanded = "?expanded=true" if expanded else ""
    catalogue_url = "http://localhost:{}/{}".format(servient.catalogue_port, expanded)
    catalogue_url_res = await http_client.fetch(catalogue_url)
    response = json.loads(catalogue_url_res.body)

    return response


async def fetch_catalogue_td(servient, thing_id):
    """Returns the TD of the given Thing recovered from the Servient TD catalogue."""

    urls_map = await fetch_catalogue(servient)
    thing_path = urls_map[thing_id].lstrip("/")
    thing_url = "http://localhost:{}/{}".format(servient.catalogue_port, thing_path)
    http_client = tornado.httpclient.AsyncHTTPClient()
    thing_url_res = await http_client.fetch(thing_url)
    response = json.loads(thing_url_res.body)

    return response


@pytest.mark.asyncio
async def test_servient_td_catalogue(servient):
    """The servient provides a Thing Description catalogue HTTP endpoint."""

    async def test_coroutine():
        wot = WoT(servient=servient)

        td_01_str = json.dumps(TD_DICT_01)
        td_02_str = json.dumps(TD_DICT_02)

        exposed_thing_01 = wot.produce(td_01_str)
        exposed_thing_02 = wot.produce(td_02_str)

        exposed_thing_01.expose()
        exposed_thing_02.expose()

        catalogue = await fetch_catalogue(servient)

        assert len(catalogue) == 2
        assert exposed_thing_01.thing.url_name in catalogue.get(TD_DICT_01["title"])
        assert exposed_thing_02.thing.url_name in catalogue.get(TD_DICT_02["title"])

        td_01_catalogue = await fetch_catalogue_td(servient, TD_DICT_01["title"])

        assert td_01_catalogue["id"] == TD_DICT_01["id"]
        assert td_01_catalogue["title"] == TD_DICT_01["title"]

        catalogue_expanded = await fetch_catalogue(servient, expanded=True)

        num_props = len(TD_DICT_01.get("properties", {}).keys())

        assert len(catalogue_expanded) == 2
        assert TD_DICT_01["title"] in catalogue_expanded
        assert TD_DICT_02["title"] in catalogue_expanded
        assert len(catalogue_expanded[TD_DICT_01["title"]]["properties"]) == num_props

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_servient_start_stop():
    """The servient and contained ExposedThings can be started and stopped."""

    fake = Faker()

    ws_port = find_free_port()
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient()
    servient.disable_td_catalogue()
    servient.add_server(ws_server)

    wot = await servient.start()

    thing_id = uuid.uuid4().urn
    title = uuid.uuid4().hex
    name_prop_string = fake.user_name()
    name_prop_boolean = fake.user_name()

    td_doc = {
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": thing_id,
        "title": title,
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc",
        "properties": {
            name_prop_string: {
                "observable": True,
                "type": "string"
            },
            name_prop_boolean: {
                "observable": True,
                "type": "boolean"
            }
        }
    }

    td_str = json.dumps(td_doc)

    exposed_thing = wot.produce(td_str)
    exposed_thing.expose()

    value_boolean = fake.pybool()
    value_string = fake.pystr()
    servient.refresh_forms()

    async def get_property(prop_name):
        """Gets the given property using the WS Link contained in the thing description."""

        td = ThingDescription.from_thing(exposed_thing.thing)
        consumed_thing = ConsumedThing(servient, td=td)

        value = await consumed_thing.read_property(prop_name)

        return value

    async def assert_thing_active():
        """Asserts that the retrieved property values are as expected."""

        retrieved_boolean = await get_property(name_prop_boolean)
        retrieved_string = await get_property(name_prop_string)

        assert retrieved_boolean == value_boolean
        assert retrieved_string == value_string

    async def test_coroutine():
        await exposed_thing.write_property(name=name_prop_boolean, value=value_boolean)
        await exposed_thing.write_property(name=name_prop_string, value=value_string)

        await assert_thing_active()

        exposed_thing.destroy()

        with pytest.raises(Exception):
            await assert_thing_active()

        with pytest.raises(Exception):
            exposed_thing.expose()

        await servient.shutdown()

    await run_test_coroutine(test_coroutine)


@pytest.mark.parametrize("servient", [{"catalogue_enabled": False}], indirect=True)
def test_duplicated_thing_names(servient):
    """A Servient rejects Things with duplicated Titles."""

    description_01 = {
        "@context": [WOT_TD_CONTEXT_URL_V1_1],
        "id": uuid.uuid4().urn,
        "title": Faker().sentence(),
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc",
    }

    description_02 = {
        "@context": [WOT_TD_CONTEXT_URL_V1_1],
        "id": uuid.uuid4().urn,
        "title": Faker().sentence(),
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc",
    }

    description_03 = {
        "@context": [WOT_TD_CONTEXT_URL_V1_1],
        "id": uuid.uuid4().urn,
        "title": description_01.get("title"),
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc",
    }

    description_01_str = json.dumps(description_01)
    description_02_str = json.dumps(description_02)
    description_03_str = json.dumps(description_03)

    wot = WoT(servient=servient)

    wot.produce(description_01_str)
    wot.produce(description_02_str)

    with pytest.raises(ValueError):
        wot.produce(description_03_str)


@pytest.mark.asyncio
async def test_catalogue_disabled_things(servient):
    """ExposedThings that have been disabled do not appear on the Servient TD catalogue."""

    async def test_coroutine():
        wot = WoT(servient=servient)

        td_01_str = json.dumps(TD_DICT_01)
        td_02_str = json.dumps(TD_DICT_02)

        wot.produce(td_01_str).expose()
        wot.produce(td_02_str)

        catalogue = await fetch_catalogue(servient)

        assert len(catalogue) == 1
        assert TD_DICT_01["title"] in catalogue

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_clients_subset():
    """Although all clients are enabled by default, the user may only enable a subset."""

    ws_client = WebsocketClient()
    servient_01 = Servient()
    servient_02 = Servient(clients=[ws_client])
    td = ThingDescription(TD_DICT_01)
    prop_name = next(iter(TD_DICT_01["properties"].keys()))

    assert servient_01.select_client(td, prop_name) is not ws_client
    assert servient_02.select_client(td, prop_name) is ws_client


@pytest.mark.asyncio
async def test_clients_config():
    """Custom configuration arguments can be passed to the Servient default protocol clients."""

    connect_timeout = random.random()
    servient = Servient(clients_config={Protocols.HTTP: {"connect_timeout": connect_timeout}})

    assert servient.clients[Protocols.HTTP].connect_timeout == connect_timeout
