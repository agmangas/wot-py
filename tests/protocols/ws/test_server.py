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
import ssl
import uuid

import pytest
import tornado.httpclient
import tornado.websocket
from faker import Faker

from tests.protocols.ws.conftest import build_websocket_url
from tests.utils import find_free_port, run_test_coroutine
from wotpy.protocols.ws.enums import WebsocketMethods, WebsocketErrors, WebsocketSchemes
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageResponse, \
    WebsocketMessageError, \
    WebsocketMessageEmittedItem
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1
from wotpy.wot.dictionaries.interaction import PropertyFragmentDict
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.thing import Thing


@pytest.mark.asyncio
async def test_thing_not_found(websocket_server):
    """The socket is automatically closed when connecting to an unknown thing."""

    ws_port = websocket_server.pop("ws_port")

    async def test_coroutine():
        url_unknown = "ws://localhost:{}/{}".format(ws_port, uuid.uuid4().hex)
        conn = await tornado.websocket.websocket_connect(url_unknown)
        msg = await conn.read_message()

        assert msg is None

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_read_property(websocket_server):
    """Properties can be retrieved using Websockets."""

    url_thing_01 = websocket_server.pop("url_thing_01")
    url_thing_02 = websocket_server.pop("url_thing_02")
    prop_name_01 = websocket_server.pop("prop_name_01")
    prop_name_02 = websocket_server.pop("prop_name_02")
    prop_name_03 = websocket_server.pop("prop_name_03")
    prop_value_01 = websocket_server.pop("prop_value_01")
    prop_value_02 = websocket_server.pop("prop_value_02")
    prop_value_03 = websocket_server.pop("prop_value_03")

    async def test_coroutine():
        conns = [
            await tornado.websocket.websocket_connect(url_thing_01),
            await tornado.websocket.websocket_connect(url_thing_02)
        ]

        request_id_01 = Faker().pyint()
        request_id_02 = Faker().pyint()
        request_id_03 = Faker().pyint()

        ws_request_prop_01 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": prop_name_01},
            msg_id=request_id_01)

        ws_request_prop_02 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": prop_name_02},
            msg_id=request_id_02)

        ws_request_prop_03 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": prop_name_03},
            msg_id=request_id_03)

        conns[0].write_message(ws_request_prop_01.to_json())
        conns[0].write_message(ws_request_prop_02.to_json())
        conns[1].write_message(ws_request_prop_03.to_json())

        raw_resp_01 = await conns[0].read_message()
        raw_resp_02 = await conns[0].read_message()
        raw_resp_03 = await conns[1].read_message()

        ws_resp_01 = WebsocketMessageResponse.from_raw(raw_resp_01)
        ws_resp_02 = WebsocketMessageResponse.from_raw(raw_resp_02)
        ws_resp_03 = WebsocketMessageResponse.from_raw(raw_resp_03)

        assert ws_resp_01.result == prop_value_01
        assert ws_resp_02.result == prop_value_02
        assert ws_resp_03.result == prop_value_03

        conns[0].close()
        conns[1].close()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_write_property(websocket_server):
    """Properties can be updated using Websockets."""

    url_thing_01 = websocket_server.pop("url_thing_01")
    exposed_thing_01 = websocket_server.pop("exposed_thing_01")
    prop_name = websocket_server.pop("prop_name_01")

    async def test_coroutine():
        conn = await tornado.websocket.websocket_connect(url_thing_01)

        updated_value = Faker().pystr()
        msg_id = uuid.uuid4().hex

        ws_request = WebsocketMessageRequest(
            method=WebsocketMethods.WRITE_PROPERTY,
            params={"name": prop_name, "value": updated_value},
            msg_id=msg_id)

        value = await exposed_thing_01.read_property(prop_name)

        assert value != updated_value

        conn.write_message(ws_request.to_json())
        raw_response = await conn.read_message()
        ws_response = WebsocketMessageResponse.from_raw(raw_response)

        assert ws_response.id == msg_id

        value = await exposed_thing_01.read_property(prop_name)

        assert value == updated_value

        ws_request_err = WebsocketMessageRequest(
            method=WebsocketMethods.WRITE_PROPERTY,
            params={"name": prop_name + Faker().pystr(), "value": updated_value},
            msg_id=msg_id)

        conn.write_message(ws_request_err.to_json())
        raw_error = await conn.read_message()
        ws_error = WebsocketMessageError.from_raw(raw_error)

        assert ws_error.code

        conn.close()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_invoke_action(websocket_server):
    """Actions can be invoked using Websockets."""

    url_thing_01 = websocket_server.pop("url_thing_01")
    exposed_thing_01 = websocket_server.pop("exposed_thing_01")
    action_name = websocket_server.pop("action_name_01")

    async def test_coroutine():
        conn = await tornado.websocket.websocket_connect(url_thing_01)

        input_val = Faker().pystr()

        expected_out = await exposed_thing_01.invoke_action(action_name, input_val)

        msg_id = Faker().pyint()

        msg_invoke_req = WebsocketMessageRequest(
            method=WebsocketMethods.INVOKE_ACTION,
            params={"name": action_name, "parameters": input_val},
            msg_id=msg_id)

        conn.write_message(msg_invoke_req.to_json())

        msg_invoke_resp_raw = await conn.read_message()
        msg_invoke_resp = WebsocketMessageResponse.from_raw(msg_invoke_resp_raw)

        assert msg_invoke_resp.id == msg_id
        assert msg_invoke_resp.result == expected_out

        conn.close()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_on_property_change(websocket_server):
    """Property changes can be observed using Websockets."""

    url_thing_01 = websocket_server.pop("url_thing_01")
    exposed_thing_01 = websocket_server.pop("exposed_thing_01")
    prop_name = websocket_server.pop("prop_name_01")

    async def test_coroutine():
        observe_msg_id = Faker().pyint()

        updated_val_01 = Faker().pystr()
        updated_val_02 = Faker().pystr()
        updated_val_03 = Faker().pystr()

        conn = await tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": prop_name},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = await conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        def assert_emitted(the_msg_raw, the_expected_val):
            msg_emitted = WebsocketMessageEmittedItem.from_raw(the_msg_raw)

            assert msg_emitted.subscription_id == subscription_id
            assert msg_emitted.data["name"] == prop_name
            assert msg_emitted.data["value"] == the_expected_val

        await exposed_thing_01.write_property(prop_name, updated_val_01)

        msg_emitted_raw = await conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_01)

        await exposed_thing_01.write_property(prop_name, updated_val_02)
        await exposed_thing_01.write_property(prop_name, updated_val_03)

        msg_emitted_raw = await conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_02)

        msg_emitted_raw = await conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_03)

        conn.close()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_on_undefined_property_change(websocket_server):
    """Observing an undefined property results in a subscription error message."""

    url_thing_01 = websocket_server.pop("url_thing_01")

    async def test_coroutine():
        observe_msg_id = Faker().pyint()
        prop_name_err = uuid.uuid4().hex

        conn = await tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": prop_name_err},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = await conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        msg_observe_err_raw = await conn.read_message()
        msg_observe_err = WebsocketMessageError.from_raw(msg_observe_err_raw)

        assert msg_observe_err.code == WebsocketErrors.SUBSCRIPTION_ERROR
        assert msg_observe_err.data["subscription"] == msg_observe_resp.result

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_on_event(websocket_server):
    """Events can be observed using Websockets."""

    url_thing_01 = websocket_server.pop("url_thing_01")
    exposed_thing_01 = websocket_server.pop("exposed_thing_01")
    event_name = websocket_server.pop("event_name_01")

    async def test_coroutine():
        observe_msg_id = Faker().pyint()
        payload_01 = Faker().pydict(10, True, [str, float])
        payload_02 = Faker().pydict(10, True, [str, float])
        payload_03 = Faker().pydict(10, True, [int])

        conn = await tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_EVENT,
            params={"name": event_name},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = await conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        def assert_emitted(the_msg_raw, the_expected_payload):
            msg_emitted = WebsocketMessageEmittedItem.from_raw(the_msg_raw)

            assert msg_emitted.subscription_id == subscription_id
            assert msg_emitted.data == the_expected_payload

        exposed_thing_01.emit_event(event_name, payload_01)

        msg_emitted_raw = await conn.read_message()
        assert_emitted(msg_emitted_raw, payload_01)

        exposed_thing_01.emit_event(event_name, payload_02)
        exposed_thing_01.emit_event(event_name, payload_03)

        msg_emitted_raw = await conn.read_message()
        assert_emitted(msg_emitted_raw, payload_02)

        msg_emitted_raw = await conn.read_message()
        assert_emitted(msg_emitted_raw, payload_03)

        conn.close()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_on_undefined_event(websocket_server):
    """Observing an undefined event results in a subscription error message."""

    url_thing_01 = websocket_server.pop("url_thing_01")

    async def test_coroutine():
        observe_msg_id = Faker().pyint()
        event_name_err = Faker().pystr()

        conn = await tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_EVENT,
            params={"name": event_name_err},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = await conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        msg_observe_err_raw = await conn.read_message()
        msg_observe_err = WebsocketMessageError.from_raw(msg_observe_err_raw)

        assert msg_observe_err.code == WebsocketErrors.SUBSCRIPTION_ERROR
        assert msg_observe_err.data["subscription"] == msg_observe_resp.result

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_dispose(websocket_server):
    """Observable subscriptions can be disposed using Websockets."""

    url_thing_01 = websocket_server.pop("url_thing_01")
    exposed_thing_01 = websocket_server.pop("exposed_thing_01")
    prop_name = websocket_server.pop("prop_name_01")

    async def test_coroutine():
        observe_msg_id = Faker().pyint()
        dispose_msg_id = Faker().pyint()

        conn = await tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": prop_name},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = await conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        await exposed_thing_01.write_property(prop_name, Faker().sentence())

        msg_emitted_raw = await conn.read_message()
        msg_emitted = WebsocketMessageEmittedItem.from_raw(msg_emitted_raw)

        assert msg_emitted.subscription_id == subscription_id

        msg_dispose_req = WebsocketMessageRequest(
            method=WebsocketMethods.DISPOSE,
            params={"subscription": subscription_id},
            msg_id=dispose_msg_id)

        conn.write_message(msg_dispose_req.to_json())

        msg_dispose_resp_raw = await conn.read_message()
        msg_dispose_resp = WebsocketMessageResponse.from_raw(msg_dispose_resp_raw)

        assert msg_dispose_resp.result == subscription_id

        conn.write_message(msg_dispose_req.to_json())

        msg_dispose_resp_02_raw = await conn.read_message()
        msg_dispose_resp_02 = WebsocketMessageResponse.from_raw(msg_dispose_resp_02_raw)

        assert not msg_dispose_resp_02.result

        await exposed_thing_01.write_property(prop_name, Faker().pystr())
        await exposed_thing_01.write_property(prop_name, Faker().pystr())

        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(
                conn.read_message(),
                timeout=0.2)

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_ssl_context(self_signed_ssl_context):
    """An SSL context can be passed to the WebSockets server to enable encryption."""

    port = find_free_port()

    title = uuid.uuid4().hex
    thing_fragment = ThingFragment({
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
        "security": "nosec_sc"
    })
    thing = Thing(thing_fragment=thing_fragment)
    exposed_thing = ExposedThing(servient=Servient(), thing=thing)

    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(prop_name, PropertyFragmentDict({
        "type": "string",
        "observable": True
    }), value=Faker().pystr())


    server = WebsocketServer(port=port, ssl_context=self_signed_ssl_context)
    server.add_exposed_thing(exposed_thing)

    async def test_coroutine():
        await server.start()

        ws_url = build_websocket_url(exposed_thing, server, port)

        assert WebsocketSchemes.WSS in ws_url

        with pytest.raises(ssl.SSLError):
            http_req = tornado.httpclient.HTTPRequest(ws_url, method="GET")
            await tornado.websocket.websocket_connect(http_req)

        http_req = tornado.httpclient.HTTPRequest(ws_url, method="GET", validate_cert=False)
        conn = await tornado.websocket.websocket_connect(http_req)

        request_id = Faker().pyint()

        msg_req = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": prop_name},
            msg_id=request_id)

        conn.write_message(msg_req.to_json())

        msg_resp_raw = await conn.read_message()
        msg_resp = WebsocketMessageResponse.from_raw(msg_resp_raw)

        assert msg_resp.id == request_id

        value = await exposed_thing.read_property(prop_name)

        assert value == msg_resp.result

        conn.close()
        await server.stop()

    await run_test_coroutine(test_coroutine)
