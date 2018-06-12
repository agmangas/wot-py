#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import uuid

# noinspection PyPackageRequirements
import pytest
import tornado.gen
import tornado.httpclient
import tornado.ioloop
import tornado.websocket
# noinspection PyPackageRequirements
from faker import Faker

from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.constants import WOT_TD_CONTEXT_URL
from wotpy.td.description import ThingDescription
from wotpy.wot.consumed import ConsumedThing
from wotpy.wot.servient import Servient


@pytest.mark.flaky(reruns=5)
def test_servient_td_catalogue():
    """The servient provides a Thing Description catalogue HTTP endpoint."""

    catalogue_port = random.randint(20000, 40000)

    servient = Servient()
    servient.enable_td_catalogue(port=catalogue_port)

    wot = servient.start()

    td_doc_01 = {
        "id": uuid.uuid4().urn,
        "name": Faker().sentence(),
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

    td_doc_02 = {
        "id": uuid.uuid4().urn,
        "name": Faker().sentence()
    }

    td_01_str = json.dumps(td_doc_01)
    td_02_str = json.dumps(td_doc_02)

    exposed_thing_01 = wot.produce(td_01_str)
    exposed_thing_02 = wot.produce(td_02_str)

    exposed_thing_01.start()
    exposed_thing_02.start()

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = tornado.httpclient.AsyncHTTPClient()

        catalogue_url = "http://localhost:{}/".format(catalogue_port)
        catalogue_url_res = yield http_client.fetch(catalogue_url)
        urls_map = json.loads(catalogue_url_res.body)

        assert len(urls_map) == 2
        assert exposed_thing_01.thing.url_name in urls_map.get(td_doc_01["id"])
        assert exposed_thing_02.thing.url_name in urls_map.get(td_doc_02["id"])

        thing_01_url = "http://localhost:{}{}".format(catalogue_port, urls_map[td_doc_01["id"]])
        thing_01_url_res = yield http_client.fetch(thing_01_url)
        td_doc_01_recovered = json.loads(thing_01_url_res.body)

        assert td_doc_01_recovered["id"] == td_doc_01["id"]
        assert td_doc_01_recovered["name"] == td_doc_01["name"]

        catalogue_expanded_url = "http://localhost:{}/?expanded=true".format(catalogue_port)
        cataligue_expanded_url_res = yield http_client.fetch(catalogue_expanded_url)
        expanded_map = json.loads(cataligue_expanded_url_res.body)

        num_props = len(td_doc_01.get("properties", {}).keys())

        assert len(expanded_map) == 2
        assert td_doc_01["id"] in expanded_map
        assert td_doc_02["id"] in expanded_map
        assert len(expanded_map[td_doc_01["id"]]["properties"]) == num_props

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_servient_start_stop():
    """The servient and contained ExposedThings can be started and stopped."""

    fake = Faker()

    ws_port = random.randint(20000, 40000)
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient()
    servient.add_server(ws_server)

    wot = servient.start()

    thing_id = uuid.uuid4().urn
    name_prop_string = fake.user_name()
    name_prop_boolean = fake.user_name()

    td_doc = {
        "id": thing_id,
        "name": Faker().sentence(),
        "properties": {
            name_prop_string: {
                "writable": True,
                "observable": True,
                "type": "string"
            },
            name_prop_boolean: {
                "writable": True,
                "observable": True,
                "type": "boolean"
            }
        }
    }

    td_str = json.dumps(td_doc)

    exposed_thing = wot.produce(td_str)
    exposed_thing.start()

    value_boolean = fake.pybool()
    value_string = fake.pystr()

    @tornado.gen.coroutine
    def get_property(prop_name):
        """Gets the given property using the WS Link contained in the thing description."""

        td = ThingDescription.from_thing(exposed_thing.thing)
        consumed_thing = ConsumedThing(servient, td=td)

        value = yield consumed_thing.read_property(prop_name)

        raise tornado.gen.Return(value)

    @tornado.gen.coroutine
    def assert_thing_active():
        """Asserts that the retrieved property values are as expected."""

        retrieved_boolean = yield get_property(name_prop_boolean)
        retrieved_string = yield get_property(name_prop_string)

        assert retrieved_boolean == value_boolean
        assert retrieved_string == value_string

    @tornado.gen.coroutine
    def test_coroutine():
        yield exposed_thing.write_property(name=name_prop_boolean, value=value_boolean)
        yield exposed_thing.write_property(name=name_prop_string, value=value_string)

        yield assert_thing_active()

        exposed_thing.stop()

        with pytest.raises(Exception):
            yield assert_thing_active()

        exposed_thing.start()

        yield assert_thing_active()

        servient.shutdown()

        with pytest.raises(Exception):
            yield assert_thing_active()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_duplicated_thing_names():
    """A Servient rejects Things with duplicated IDs."""

    description_01 = {
        "@context": [WOT_TD_CONTEXT_URL],
        "id": uuid.uuid4().urn,
        "name": Faker().sentence()
    }

    description_02 = {
        "@context": [WOT_TD_CONTEXT_URL],
        "id": uuid.uuid4().urn,
        "name": Faker().sentence()
    }

    description_03 = {
        "@context": [WOT_TD_CONTEXT_URL],
        "id": description_01.get("id"),
        "name": Faker().sentence()
    }

    description_01_str = json.dumps(description_01)
    description_02_str = json.dumps(description_02)
    description_03_str = json.dumps(description_03)

    servient = Servient()
    wot = servient.start()

    wot.produce(description_01_str)
    wot.produce(description_02_str)

    with pytest.raises(ValueError):
        wot.produce(description_03_str)
