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
import json

import aiocoap
import pytest
from faker import Faker

from tests.utils import find_free_port, run_test_coroutine
from wotpy.protocols.coap.server import CoAPServer
from wotpy.protocols.enums import InteractionVerbs
from wotpy.wot.dictionaries.interaction import ActionFragmentDict


def _get_property_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property read/write href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("127.0.0.1", prop)
    return next(item.href for item in prop_forms if InteractionVerbs.READ_PROPERTY == item.op)


def _get_property_observe_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property subscription href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("127.0.0.1", prop)
    return next(item.href for item in prop_forms if InteractionVerbs.OBSERVE_PROPERTY == item.op)


def _get_action_href(exp_thing, action_name, server):
    """Helper function to retrieve the Action invocation href."""

    action = exp_thing.thing.actions[action_name]
    action_forms = server.build_forms("127.0.0.1", action)
    return next(item.href for item in action_forms if InteractionVerbs.INVOKE_ACTION == item.op)


def _get_event_href(exp_thing, event_name, server):
    """Helper function to retrieve the Event subscription href."""

    event = exp_thing.thing.events[event_name]
    event_forms = server.build_forms("127.0.0.1", event)
    return next(item.href for item in event_forms if InteractionVerbs.SUBSCRIBE_EVENT == item.op)


async def _next_observation(request):
    """Yields the next observation for the given CoAP request."""

    resp = await request.observation.__aiter__().__anext__()
    val = json.loads(resp.payload)
    return val


@pytest.mark.asyncio
async def test_start_stop():
    """The CoAP server can be started and stopped."""

    coap_port = find_free_port()
    coap_server = CoAPServer(port=coap_port)
    ping_uri = "coap://127.0.0.1:{}/.well-known/core".format(coap_port)

    async def ping():
        try:
            coap_client = await aiocoap.Context.create_client_context()
            request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=ping_uri)
            response = await asyncio.wait_for(
                coap_client.request(request_msg).response,
                timeout=2)
        except Exception:
            return False
        finally:
            await coap_client.shutdown()

        return response.code.is_successful()

    async def test_coroutine():
        assert not (await ping())

        await coap_server.start()

        assert await ping()
        assert await ping()

        for _ in range(5):
            await coap_server.stop()

        assert not (await ping())

        await coap_server.stop()

        for _ in range(5):
            await coap_server.start()

        assert await ping()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_property_read(coap_server):
    """Properties exposed in an CoAP server can be read with a CoAP GET request."""

    exposed_thing = next(coap_server.exposed_things)
    prop_name = next(iter(exposed_thing.thing.properties.keys()))
    href = _get_property_href(exposed_thing, prop_name, coap_server)

    async def test_coroutine():
        prop_value = Faker().pyint()
        await exposed_thing.properties[prop_name].write(prop_value)
        coap_client = await aiocoap.Context.create_client_context()
        request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href)
        response = await coap_client.request(request_msg).response

        assert response.code.is_successful()
        assert json.loads(response.payload).get("value") == prop_value
        await coap_client.shutdown()


    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_property_write(coap_server):
    """Properties exposed in an CoAP server can be updated with a CoAP POST request."""

    exposed_thing = next(coap_server.exposed_things)
    prop_name = next(iter(exposed_thing.thing.properties.keys()))
    href = _get_property_href(exposed_thing, prop_name, coap_server)

    async def test_coroutine():
        value_old = Faker().pyint()
        value_new = Faker().pyint()
        await exposed_thing.properties[prop_name].write(value_old)
        coap_client = await aiocoap.Context.create_client_context()
        payload = json.dumps({"value": value_new}).encode("utf-8")
        request_msg = aiocoap.Message(code=aiocoap.Code.PUT, payload=payload, uri=href)
        response = await coap_client.request(request_msg).response

        assert response.code.is_successful()
        assert (await exposed_thing.properties[prop_name].read()) == value_new
        await coap_client.shutdown()


    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_property_subscription(coap_server):
    """Properties exposed in an CoAP server can be observed for value updates."""

    exposed_thing = next(coap_server.exposed_things)
    prop_name = next(iter(exposed_thing.thing.properties.keys()))
    href = _get_property_observe_href(exposed_thing, prop_name, coap_server)

    future_values = [Faker().pyint() for _ in range(5)]

    async def update_property():
        while True:
            await exposed_thing.properties[prop_name].write(future_values[0])
            await asyncio.sleep(0.005)

    def all_values_written():
        return len(future_values) == 0

    async def test_coroutine():
        task = asyncio.create_task(update_property())

        coap_client = await aiocoap.Context.create_client_context()
        request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href, observe=0)
        request = coap_client.request(request_msg)

        while not all_values_written():
            payload = await asyncio.ensure_future(_next_observation(request))
            value = payload.get("value")

            try:
                future_values.pop(future_values.index(value))
            except ValueError:
                pass

        request.observation.cancel()
        task.cancel()
        await coap_client.shutdown()

    await run_test_coroutine(test_coroutine)


async def _test_action_invoke(the_coap_server, input_value=None, invocation_sleep=0.05):
    """Helper function to invoke an Action in the CoAP server."""

    exposed_thing = next(the_coap_server.exposed_things)
    action_name = next(iter(exposed_thing.thing.actions.keys()))
    href = _get_action_href(exposed_thing, action_name, the_coap_server)

    coap_client = await aiocoap.Context.create_client_context()

    input_value = input_value if input_value is not None else Faker().pyint()
    payload = json.dumps({"input": input_value}).encode("utf-8")
    msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
    response = await coap_client.request(msg).response
    invocation_id = json.loads(response.payload).get("id")

    assert response.code.is_successful()
    assert invocation_id

    await asyncio.sleep(invocation_sleep)

    obsv_payload = json.dumps({"id": invocation_id}).encode("utf-8")
    obsv_msg = aiocoap.Message(code=aiocoap.Code.GET, payload=obsv_payload, uri=href, observe=0)
    obsv_request = coap_client.request(obsv_msg)
    obsv_response = await obsv_request.response

    if not obsv_request.observation.cancelled:
        obsv_request.observation.cancel()

    await coap_client.shutdown()

    return obsv_response


@pytest.mark.asyncio
async def test_action_invoke(coap_server):
    """Actions exposed in a CoAP server can be invoked."""

    async def test_coroutine():
        input_value = Faker().pyint()
        response = await _test_action_invoke(coap_server, input_value=input_value)
        data = json.loads(response.payload)

        assert response.code.is_successful()
        assert data.get("done") is True
        assert data.get("error", None) is None
        assert data.get("result") == input_value * 3

    await run_test_coroutine(test_coroutine)


@pytest.mark.parametrize("coap_server", [{"action_clear_ms": 5}], indirect=True)
@pytest.mark.asyncio
async def test_action_clear_invocation(coap_server):
    """Completed Action invocations are removed from the CoAP server after a while."""

    async def test_coroutine():
        invocation_sleep_secs = 0.1
        assert (invocation_sleep_secs * 1000) > coap_server.action_clear_ms
        response = await _test_action_invoke(coap_server, invocation_sleep=invocation_sleep_secs)
        assert not response.code.is_successful()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_action_invoke_parallel(coap_server):
    """Actions exposed in a CoAP server can be invoked in parallel."""

    exposed_thing = next(coap_server.exposed_things)
    action_name = Faker().pystr()

    handler_futures = {}

    async def handler(parameters):
        inp = parameters["input"]
        await handler_futures[inp.get("future")]
        return inp.get("number") * 3

    port = coap_server.port
    exposed_thing.add_action(action_name, ActionFragmentDict({
        "input": {"type": "object"},
        "output": {"type": "number"}
    }), handler)

    href = _get_action_href(exposed_thing, action_name, coap_server)

    async def invoke_action(coap_client):
        input_num = Faker().pyint()
        future_id = Faker().pystr()
        loop = asyncio.get_running_loop()
        handler_futures[future_id] = loop.create_future()

        payload = json.dumps({"input": {
            "number": input_num,
            "future": future_id
        }}).encode("utf-8")

        msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
        response = await coap_client.request(msg).response
        assert response.code.is_successful()
        invocation_id = json.loads(response.payload).get("id")

        return {
            "number": input_num,
            "future": future_id,
            "id": invocation_id
        }

    def build_observe_request(coap_client, invocation):
        payload = json.dumps({"id": invocation["id"]}).encode("utf-8")
        msg = aiocoap.Message(code=aiocoap.Code.GET, payload=payload, uri=href, observe=0)
        return coap_client.request(msg)

    async def test_coroutine():
        coap_client = await aiocoap.Context.create_client_context()

        invocation_01 = await invoke_action(coap_client)
        invocation_02 = await invoke_action(coap_client)

        def unblock_01():
            handler_futures[invocation_01["future"]].set_result(True)

        def unblock_02():
            handler_futures[invocation_02["future"]].set_result(True)

        observe_req_01 = build_observe_request(coap_client, invocation_01)
        observe_req_02 = build_observe_request(coap_client, invocation_02)

        first_resp_01 = await observe_req_01.response
        first_resp_02 = await observe_req_02.response

        assert json.loads(first_resp_01.payload).get("done") is False
        assert json.loads(first_resp_02.payload).get("done") is False

        assert not handler_futures[invocation_01["future"]].done()
        assert not handler_futures[invocation_02["future"]].done()

        async def wait_for_result(observe_req):
            res = None

            while not res or not res.get("done", False):
                res = await asyncio.ensure_future(_next_observation(observe_req))

            return res

        fut_result_01 = asyncio.ensure_future(wait_for_result(observe_req_01))
        fut_result_02 = asyncio.ensure_future(wait_for_result(observe_req_02))

        unblock_01()

        result_01 = await fut_result_01

        assert result_01.get("done") is True
        assert result_01.get("id") == invocation_01.get("id")
        assert result_01.get("result") == invocation_01.get("number") * 3

        assert not fut_result_02.done()

        unblock_02()

        result_02 = await fut_result_02

        assert result_02.get("done") is True
        assert result_02.get("id") == invocation_02.get("id")
        assert result_02.get("result") == invocation_02.get("number") * 3

        observe_req_01.observation.cancel()
        observe_req_02.observation.cancel()

        await coap_client.shutdown()

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_event_subscription(coap_server):
    """Event emissions can be observed in a CoAP server."""

    exposed_thing = next(coap_server.exposed_things)
    event_name = next(iter(exposed_thing.thing.events.keys()))
    href = _get_event_href(exposed_thing, event_name, coap_server)

    emitted_values = [{
        "num": Faker().pyint(),
        "str": Faker().sentence()
    } for _ in range(5)]

    async def emit_event():
        while True:
            exposed_thing.emit_event(event_name, payload=emitted_values[0])
            await asyncio.sleep(0.005)

    def all_values_emitted():
        return len(emitted_values) == 0

    async def test_coroutine():
        task = asyncio.create_task(emit_event())

        coap_client = await aiocoap.Context.create_client_context()
        request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href, observe=0)
        request = coap_client.request(request_msg)
        first_response = await request.response

        assert not first_response.payload

        while not all_values_emitted():
            payload = await asyncio.ensure_future(_next_observation(request))
            data = payload["data"]

            assert payload.get("name") == event_name
            assert "num" in data
            assert "str" in data

            try:
                emitted_idx = next(
                    idx for idx, item in enumerate(emitted_values)
                    if item["num"] == data["num"] and item["str"] == data["str"])

                emitted_values.pop(emitted_idx)
            except StopIteration:
                pass

        request.observation.cancel()
        task.cancel()
        await coap_client.shutdown()

    await run_test_coroutine(test_coroutine)
