#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random

# noinspection PyPackageRequirements
import pytest
import tornado.gen
import tornado.httpclient
import tornado.ioloop
import tornado.websocket
# noinspection PyCompatibility
from concurrent.futures import Future
# noinspection PyPackageRequirements
from faker import Faker

from wotpy.protocols.enums import Protocols
from wotpy.protocols.ws.enums import WebsocketMethods
from wotpy.protocols.ws.messages import WebsocketMessageRequest, WebsocketMessageResponse
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.constants import WOT_TD_CONTEXT_URL
from wotpy.td.enums import InteractionTypes
from wotpy.wot.servient import Servient


@pytest.mark.flaky(reruns=5)
def test_servient_td_catalogue():
    """The servient provides a Thing Description catalogue HTTP endpoint."""

    fake = Faker()

    catalogue_port = random.randint(20000, 40000)
    catalogue_url = "http://localhost:{}/".format(catalogue_port)

    servient = Servient()
    servient.enable_td_catalogue(port=catalogue_port)

    wot = servient.start()

    description_01 = {
        "@context": [WOT_TD_CONTEXT_URL],
        "name": fake.user_name(),
        "interaction": [{
            "@type": [InteractionTypes.PROPERTY],
            "name": fake.user_name(),
            "outputData": {"type": "string"},
            "writable": True,
            "observable": True
        }]
    }

    description_02 = {
        "@context": [WOT_TD_CONTEXT_URL],
        "name": fake.user_name(),
        "interaction": []
    }

    description_01_str = json.dumps(description_01)
    description_02_str = json.dumps(description_02)

    exposed_thing_01 = wot.produce(description_01_str)
    exposed_thing_02 = wot.produce(description_02_str)

    exposed_thing_01.start()
    exposed_thing_02.start()

    io_loop = tornado.ioloop.IOLoop.current()

    future_result = Future()

    @tornado.gen.coroutine
    def get_catalogue():
        """Fetches the TD catalogue and verifies its contents."""

        try:
            http_client = tornado.httpclient.AsyncHTTPClient()
            catalogue_result = yield http_client.fetch(catalogue_url)
            descriptions_map = json.loads(catalogue_result.body)

            assert len(descriptions_map) == 2
            assert description_01["name"] in descriptions_map
            assert description_02["name"] in descriptions_map
            assert len(descriptions_map[description_01["name"]]["interaction"]) == 1

            future_result.set_result(True)
        except Exception as ex:
            future_result.set_exception(ex)

    @tornado.gen.coroutine
    def stop_loop():
        """Stops the IOLoop when the result Future completes."""

        # noinspection PyBroadException
        try:
            yield future_result
        except:
            pass

        io_loop.stop()

    io_loop.add_callback(get_catalogue)
    io_loop.add_callback(stop_loop)
    io_loop.start()

    assert future_result.result() is True


@pytest.mark.flaky(reruns=5)
def test_servient_start_stop():
    """The servient and contained ExposedThings can be started and stopped."""

    fake = Faker()

    ws_port = random.randint(20000, 40000)
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient()
    servient.add_server(ws_server)

    wot = servient.start()

    name_thing = fake.user_name()
    name_prop_boolean = fake.user_name()
    name_prop_string = fake.user_name()

    description = {
        "@context": [WOT_TD_CONTEXT_URL],
        "name": name_thing,
        "interaction": [{
            "@type": [InteractionTypes.PROPERTY],
            "name": name_prop_boolean,
            "outputData": {"type": "boolean"},
            "writable": True,
            "observable": True
        }, {
            "@type": [InteractionTypes.PROPERTY],
            "name": name_prop_string,
            "outputData": {"type": "string"},
            "writable": True,
            "observable": True
        }]
    }

    description_str = json.dumps(description)

    exposed_thing = wot.produce(description_str)
    exposed_thing.start()

    value_boolean = fake.pybool()
    value_string = fake.pystr()

    assert exposed_thing.write_property(name=name_prop_boolean, value=value_boolean).done()
    assert exposed_thing.write_property(name=name_prop_string, value=value_string).done()

    io_loop = tornado.ioloop.IOLoop.current()

    future_result = Future()

    @tornado.gen.coroutine
    def get_property(prop_name):
        """Gets the given property using the WS Link contained in the thing description."""

        prop = exposed_thing.thing.find_interaction(name=prop_name)

        assert len(prop.forms)

        prop_protocols = [item.protocol for item in prop.forms]

        assert Protocols.WEBSOCKETS in prop_protocols

        link = next(item for item in prop.forms if item.protocol == Protocols.WEBSOCKETS)
        conn = yield tornado.websocket.websocket_connect(link.href)

        msg_set_req = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": prop_name},
            msg_id=fake.pyint())

        conn.write_message(msg_set_req.to_json())

        msg_get_resp_raw = yield conn.read_message()
        msg_get_resp = WebsocketMessageResponse.from_raw(msg_get_resp_raw)

        assert msg_get_resp.msg_id == msg_set_req.msg_id

        raise tornado.gen.Return(msg_get_resp.result)

    @tornado.gen.coroutine
    def assert_get_properties():
        """Asserts that the retrieved property values are as expected."""

        retrieved_boolean = yield get_property(name_prop_boolean)
        retrieved_string = yield get_property(name_prop_string)

        assert retrieved_boolean == value_boolean
        assert retrieved_string == value_string

    @tornado.gen.coroutine
    def run_test_coroutines():
        """Gets the properties under multiple conditions
        to verify servient behaviour on start and stop."""

        try:
            yield assert_get_properties()

            exposed_thing.stop()

            with pytest.raises(Exception):
                yield assert_get_properties()

            exposed_thing.start()

            yield assert_get_properties()

            servient.shutdown()

            with pytest.raises(Exception):
                yield assert_get_properties()

            future_result.set_result(True)
        except Exception as ex:
            future_result.set_exception(ex)

    @tornado.gen.coroutine
    def stop_loop():
        """Stops the IOLoop when the result Future completes."""

        # noinspection PyBroadException
        try:
            yield future_result
        except:
            pass

        io_loop.stop()

    io_loop.add_callback(run_test_coroutines)
    io_loop.add_callback(stop_loop)
    io_loop.start()

    assert future_result.result() is True
