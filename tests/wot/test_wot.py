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

import asyncio
import json
import uuid

import pytest
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from tests.utils import find_free_port, run_test_coroutine
from tests.wot.utils import assert_exposed_thing_equal
from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1
from wotpy.wot.dictionaries.filter import ThingFilterDict
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.enums import DiscoveryMethod
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.wot import WoT

TIMEOUT_DISCOVER = 5


@pytest.mark.asyncio
async def test_produce_model_str():
    """Things can be produced from TD documents serialized to JSON-LD string."""

    td_str = json.dumps(TD_EXAMPLE)
    thing_id = TD_EXAMPLE.get("id")
    thing_title = TD_EXAMPLE.get("title")

    servient = Servient()
    wot = WoT(servient=servient)

    assert wot.servient is servient

    exp_thing = wot.produce(td_str)

    assert servient.get_exposed_thing(thing_title)
    assert exp_thing.thing.id == thing_id
    assert_exposed_thing_equal(exp_thing, TD_EXAMPLE)


@pytest.mark.asyncio
async def test_produce_model_thing_template():
    """Things can be produced from ThingTemplate instances."""

    thing_id = Faker().url()
    thing_title = Faker().sentence()

    thing_template = ThingFragment({
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": thing_id,
        "title": thing_title,
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc"
    })

    servient = Servient()
    wot = WoT(servient=servient)

    exp_thing = wot.produce(thing_template)

    assert servient.get_exposed_thing(thing_title)
    assert exp_thing.id == thing_id
    assert exp_thing.title == thing_title


@pytest.mark.asyncio
async def test_produce_model_consumed_thing():
    """Things can be produced from ConsumedThing instances."""

    servient = Servient()
    wot = WoT(servient=servient)

    td_str = json.dumps(TD_EXAMPLE)
    consumed_thing = wot.consume(td_str)
    exposed_thing = wot.produce(consumed_thing)

    assert exposed_thing.id == consumed_thing.td.id
    assert exposed_thing.title == consumed_thing.td.title
    assert len(exposed_thing.properties) == len(consumed_thing.td.properties)
    assert len(exposed_thing.actions) == len(consumed_thing.td.actions)
    assert len(exposed_thing.events) == len(consumed_thing.td.events)


@pytest.mark.asyncio
async def test_produce_from_url(td_example_tornado_app):
    """ExposedThings can be created from URLs that provide Thing Description documents."""

    app_port = find_free_port()
    td_example_tornado_app.listen(app_port)

    url_valid = "http://localhost:{}/".format(app_port)
    url_error = "http://localhost:{}/{}".format(app_port, Faker().pystr())

    wot = WoT(servient=Servient())

    async def test_coroutine():
        exposed_thing = await wot.produce_from_url(url_valid)

        assert exposed_thing.thing.id == TD_EXAMPLE.get("id")

        with pytest.raises(Exception):
            await wot.produce_from_url(url_error)

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_consume_from_url(td_example_tornado_app):
    """ConsumedThings can be created from URLs that provide Thing Description documents."""

    app_port = find_free_port()
    td_example_tornado_app.listen(app_port)

    url_valid = "http://localhost:{}/".format(app_port)
    url_error = "http://localhost:{}/{}".format(app_port, Faker().pystr())

    wot = WoT(servient=Servient())

    async def test_coroutine():
        consumed_thing = await wot.consume_from_url(url_valid)

        assert consumed_thing.td.id == TD_EXAMPLE.get("id")

        with pytest.raises(Exception):
            await wot.consume_from_url(url_error)

    await run_test_coroutine(test_coroutine)


TD_DICT_01 = {
    "@context": [
        WOT_TD_CONTEXT_URL_V1_1,
    ],
    "id": uuid.uuid4().urn,
    "title": Faker().pystr(),
    "security": ["psk_sc"],
    "securityDefinitions": {
        "psk_sc": {"scheme": "psk"}
    },
    "version": {"instance": "1.2.1"},
    "properties": {
        "status": {
            "description": Faker().pystr(),
            "type": "string",
            "forms": [{
                "contentType": "application/json",
                "href": "http://127.0.0.1/status",
                "op": ["readproperty", "writeproperty"]
            }]
        }
    }
}

TD_DICT_02 = {
    "@context": [
        WOT_TD_CONTEXT_URL_V1_1,
    ],
    "id": uuid.uuid4().urn,
    "title": Faker().pystr(),
    "securityDefinitions": {
        "nosec_sc":{
            "scheme":"nosec"
        }
    },
    "security": "nosec_sc",
    "version": {"instance": "2.0.0"},
    "actions": {
        "toggle": {
            "output": {"type": "boolean"},
            "forms": [{
                "contentType": "application/json",
                "href": "http://127.0.0.1/toggle",
                "op": "invokeaction"
            }]
        }
    }
}


def assert_equal_tds(one, other):
    """Asserts that both TDs are equal."""

    one = ThingDescription(one) if not isinstance(one, ThingDescription) else one
    other = ThingDescription(other) if not isinstance(other, ThingDescription) else other
    assert one.to_dict() == other.to_dict()


def assert_equal_td_sequences(tds, td_dicts):
    """Asserts that the given sequences ot TDs and TD dicts are equal."""

    assert len(tds) == len(td_dicts)

    for td_dict in td_dicts:
        td_match = next(td.to_dict() for td in tds if td.id == td_dict["id"])
        assert_equal_tds(td_match, td_dict)


@pytest.mark.asyncio
async def test_discovery_method_local():
    """All TDs contained in the Servient are returned when using the local
    discovery method without defining the fragment nor the query fields."""

    servient = Servient()
    wot = WoT(servient=servient)
    wot.produce(ThingFragment(TD_DICT_01))
    wot.produce(ThingFragment(TD_DICT_02))

    def resolve(future_done, found):
        len(found) == 2 and not future_done.done() and future_done.set_result(True)

    async def test_coroutine():
        loop = asyncio.get_running_loop()
        future_done, found = loop.create_future(), []

        thing_filter = ThingFilterDict(method=DiscoveryMethod.LOCAL)
        observable = wot.discover(thing_filter)

        subscription = observable.subscribe(
            on_next=lambda td_str:
            found.append(ThingDescription(td_str)) or resolve(future_done, found))

        await future_done

        assert_equal_td_sequences(found, [TD_DICT_01, TD_DICT_02])

        subscription.dispose()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_discovery_fragment():
    """The Thing filter fragment attribute enables discovering Things by matching TD fields."""

    servient = Servient()
    wot = WoT(servient=servient)
    wot.produce(ThingFragment(TD_DICT_01))
    wot.produce(ThingFragment(TD_DICT_02))

    async def test_coroutine():
        async def first(thing_filter):
            """Returns the first TD discovery for the given Thing filter."""

            def resolve(future_done):
                not future_done.done() and future_done.set_result(True)

            async def discover_first():
                loop = asyncio.get_running_loop()
                future_done, found = loop.create_future(), []

                observable = wot.discover(thing_filter)

                subscription = observable.subscribe(
                    on_next=lambda td_str:
                    found.append(ThingDescription(td_str)) or resolve(future_done))

                await future_done

                subscription.dispose()

                assert len(found)

                return found[0]

            thing = asyncio.create_task(discover_first())
            return await asyncio.wait_for(thing, timeout=TIMEOUT_DISCOVER)

        fragment_td_pairs = [
            ({"title": TD_DICT_01.get("title")}, TD_DICT_01),
            ({"version": {"instance": "2.0.0"}}, TD_DICT_02),
            ({"id": TD_DICT_02.get("id")}, TD_DICT_02),
            ({"securityDefinitions": {"psk_sc": {"scheme": "psk"}}}, TD_DICT_01)
        ]

        for fragment, td_expected in fragment_td_pairs:
            td_found = await first(ThingFilterDict(method=DiscoveryMethod.LOCAL, fragment=fragment))
            assert_equal_tds(td_found, td_expected)

    await run_test_coroutine(test_coroutine)
