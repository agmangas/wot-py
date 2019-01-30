#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import uuid

import pytest
import six
import tornado.gen
import tornado.httpclient
import tornado.ioloop
import tornado.websocket
from faker import Faker

from tests.utils import find_free_port, run_test_coroutine
from wotpy.protocols.enums import Protocols
from wotpy.protocols.ws.client import WebsocketClient
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.constants import WOT_TD_CONTEXT_URL
from wotpy.wot.consumed.thing import ConsumedThing
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.wot import WoT

TD_DICT_01 = {
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

TD_DICT_02 = {
    "id": uuid.uuid4().urn,
    "name": Faker().sentence()
}


@tornado.gen.coroutine
def fetch_catalogue(servient, expanded=False):
    """Returns the TD catalogue exposed by the given Servient."""

    http_client = tornado.httpclient.AsyncHTTPClient()
    expanded = "?expanded=true" if expanded else ""
    catalogue_url = "http://localhost:{}/{}".format(servient.catalogue_port, expanded)
    catalogue_url_res = yield http_client.fetch(catalogue_url)
    response = json.loads(catalogue_url_res.body)

    raise tornado.gen.Return(response)


@tornado.gen.coroutine
def fetch_catalogue_td(servient, thing_id):
    """Returns the TD of the given Thing recovered from the Servient TD catalogue."""

    urls_map = yield fetch_catalogue(servient)
    thing_path = urls_map[thing_id].lstrip("/")
    thing_url = "http://localhost:{}/{}".format(servient.catalogue_port, thing_path)
    http_client = tornado.httpclient.AsyncHTTPClient()
    thing_url_res = yield http_client.fetch(thing_url)
    response = json.loads(thing_url_res.body)

    raise tornado.gen.Return(response)


def test_servient_td_catalogue(servient):
    """The servient provides a Thing Description catalogue HTTP endpoint."""

    @tornado.gen.coroutine
    def test_coroutine():
        wot = WoT(servient=servient)

        td_01_str = json.dumps(TD_DICT_01)
        td_02_str = json.dumps(TD_DICT_02)

        exposed_thing_01 = wot.produce(td_01_str)
        exposed_thing_02 = wot.produce(td_02_str)

        exposed_thing_01.expose()
        exposed_thing_02.expose()

        catalogue = yield fetch_catalogue(servient)

        assert len(catalogue) == 2
        assert exposed_thing_01.thing.url_name in catalogue.get(TD_DICT_01["id"])
        assert exposed_thing_02.thing.url_name in catalogue.get(TD_DICT_02["id"])

        td_01_catalogue = yield fetch_catalogue_td(servient, TD_DICT_01["id"])

        assert td_01_catalogue["id"] == TD_DICT_01["id"]
        assert td_01_catalogue["name"] == TD_DICT_01["name"]

        catalogue_expanded = yield fetch_catalogue(servient, expanded=True)

        num_props = len(TD_DICT_01.get("properties", {}).keys())

        assert len(catalogue_expanded) == 2
        assert TD_DICT_01["id"] in catalogue_expanded
        assert TD_DICT_02["id"] in catalogue_expanded
        assert len(catalogue_expanded[TD_DICT_01["id"]]["properties"]) == num_props

    run_test_coroutine(test_coroutine)


def test_servient_start_stop():
    """The servient and contained ExposedThings can be started and stopped."""

    fake = Faker()

    ws_port = find_free_port()
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient()
    servient.disable_td_catalogue()
    servient.add_server(ws_server)

    @tornado.gen.coroutine
    def start():
        raise tornado.gen.Return((yield servient.start()))

    wot = tornado.ioloop.IOLoop.current().run_sync(start)

    thing_id = uuid.uuid4().urn
    name_prop_string = fake.user_name()
    name_prop_boolean = fake.user_name()

    td_doc = {
        "id": thing_id,
        "name": Faker().sentence(),
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

        exposed_thing.destroy()

        with pytest.raises(Exception):
            yield assert_thing_active()

        with pytest.raises(Exception):
            exposed_thing.expose()

        yield servient.shutdown()

    run_test_coroutine(test_coroutine)


@pytest.mark.parametrize("servient", [{"catalogue_enabled": False}], indirect=True)
def test_duplicated_thing_names(servient):
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

    wot = WoT(servient=servient)

    wot.produce(description_01_str)
    wot.produce(description_02_str)

    with pytest.raises(ValueError):
        wot.produce(description_03_str)


def test_catalogue_disabled_things(servient):
    """ExposedThings that have been disabled do not appear on the Servient TD catalogue."""

    @tornado.gen.coroutine
    def test_coroutine():
        wot = WoT(servient=servient)

        td_01_str = json.dumps(TD_DICT_01)
        td_02_str = json.dumps(TD_DICT_02)

        wot.produce(td_01_str).expose()
        wot.produce(td_02_str)

        catalogue = yield fetch_catalogue(servient)

        assert len(catalogue) == 1
        assert TD_DICT_01["id"] in catalogue

    run_test_coroutine(test_coroutine)


def test_clients_subset():
    """Although all clients are enabled by default, the user may only enable a subset."""

    ws_client = WebsocketClient()
    servient_01 = Servient()
    servient_02 = Servient(clients=[ws_client])
    td = ThingDescription(TD_DICT_01)
    prop_name = next(six.iterkeys(TD_DICT_01["properties"]))

    assert servient_01.select_client(td, prop_name) is not ws_client
    assert servient_02.select_client(td, prop_name) is ws_client


def test_clients_config():
    """Custom configuration arguments can be passed to the Servient default protocol clients."""

    connect_timeout = random.random()
    servient = Servient(clients_config={Protocols.HTTP: {"connect_timeout": connect_timeout}})

    assert servient.clients[Protocols.HTTP].connect_timeout == connect_timeout
