#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json

import aiocoap
import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
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


@tornado.gen.coroutine
def _next_observation(request):
    """Yields the next observation for the given CoAP request."""

    resp = yield request.observation.__aiter__().__anext__()
    val = json.loads(resp.payload)
    raise tornado.gen.Return(val)


def test_start_stop():
    """The CoAP server can be started and stopped."""

    coap_port = find_free_port()
    coap_server = CoAPServer(port=coap_port)
    ping_uri = "coap://127.0.0.1:{}/.well-known/core".format(coap_port)

    @tornado.gen.coroutine
    def ping():
        try:
            coap_client = yield aiocoap.Context.create_client_context()
            request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=ping_uri)
            response = yield tornado.gen.with_timeout(
                datetime.timedelta(seconds=2),
                coap_client.request(request_msg).response)
        except Exception:
            raise tornado.gen.Return(False)

        raise tornado.gen.Return(response.code.is_successful())

    @tornado.gen.coroutine
    def test_coroutine():
        assert not (yield ping())

        yield coap_server.start()

        assert (yield ping())
        assert (yield ping())

        for _ in range(5):
            yield coap_server.stop()

        assert not (yield ping())

        yield coap_server.stop()

        for _ in range(5):
            yield coap_server.start()

        assert (yield ping())

    run_test_coroutine(test_coroutine)


def test_property_read(coap_server):
    """Properties exposed in an CoAP server can be read with a CoAP GET request."""

    exposed_thing = next(coap_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    href = _get_property_href(exposed_thing, prop_name, coap_server)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_value = Faker().pyint()
        yield exposed_thing.properties[prop_name].write(prop_value)
        coap_client = yield aiocoap.Context.create_client_context()
        request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href)
        response = yield coap_client.request(request_msg).response

        assert response.code.is_successful()
        assert json.loads(response.payload).get("value") == prop_value

    run_test_coroutine(test_coroutine)


def test_property_write(coap_server):
    """Properties exposed in an CoAP server can be updated with a CoAP POST request."""

    exposed_thing = next(coap_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    href = _get_property_href(exposed_thing, prop_name, coap_server)

    @tornado.gen.coroutine
    def test_coroutine():
        value_old = Faker().pyint()
        value_new = Faker().pyint()
        yield exposed_thing.properties[prop_name].write(value_old)
        coap_client = yield aiocoap.Context.create_client_context()
        payload = json.dumps({"value": value_new}).encode("utf-8")
        request_msg = aiocoap.Message(code=aiocoap.Code.PUT, payload=payload, uri=href)
        response = yield coap_client.request(request_msg).response

        assert response.code.is_successful()
        assert (yield exposed_thing.properties[prop_name].read()) == value_new

    run_test_coroutine(test_coroutine)


def test_property_subscription(coap_server):
    """Properties exposed in an CoAP server can be observed for value updates."""

    exposed_thing = next(coap_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    href = _get_property_observe_href(exposed_thing, prop_name, coap_server)

    future_values = [Faker().pyint() for _ in range(5)]

    @tornado.gen.coroutine
    def update_property():
        yield exposed_thing.properties[prop_name].write(future_values[0])

    def all_values_written():
        return len(future_values) == 0

    @tornado.gen.coroutine
    def test_coroutine():
        periodic_set = tornado.ioloop.PeriodicCallback(update_property, 5)
        periodic_set.start()

        coap_client = yield aiocoap.Context.create_client_context()
        request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href, observe=0)
        request = coap_client.request(request_msg)

        while not all_values_written():
            payload = yield _next_observation(request)
            value = payload.get("value")

            try:
                future_values.pop(future_values.index(value))
            except ValueError:
                pass

        request.observation.cancel()
        periodic_set.stop()

    run_test_coroutine(test_coroutine)


@tornado.gen.coroutine
def _test_action_invoke(the_coap_server, input_value=None, invocation_sleep=0.05):
    """Helper function to invoke an Action in the CoAP server."""

    exposed_thing = next(the_coap_server.exposed_things)
    action_name = next(six.iterkeys(exposed_thing.thing.actions))
    href = _get_action_href(exposed_thing, action_name, the_coap_server)

    coap_client = yield aiocoap.Context.create_client_context()

    input_value = input_value if input_value is not None else Faker().pyint()
    payload = json.dumps({"input": input_value}).encode("utf-8")
    msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
    response = yield coap_client.request(msg).response
    invocation_id = json.loads(response.payload).get("id")

    assert response.code.is_successful()
    assert invocation_id

    yield tornado.gen.sleep(invocation_sleep)

    obsv_payload = json.dumps({"id": invocation_id}).encode("utf-8")
    obsv_msg = aiocoap.Message(code=aiocoap.Code.GET, payload=obsv_payload, uri=href, observe=0)
    obsv_request = coap_client.request(obsv_msg)
    obsv_response = yield obsv_request.response

    if not obsv_request.observation.cancelled:
        obsv_request.observation.cancel()

    raise tornado.gen.Return(obsv_response)


def test_action_invoke(coap_server):
    """Actions exposed in a CoAP server can be invoked."""

    @tornado.gen.coroutine
    def test_coroutine():
        input_value = Faker().pyint()
        response = yield _test_action_invoke(coap_server, input_value=input_value)
        data = json.loads(response.payload)

        assert response.code.is_successful()
        assert data.get("done") is True
        assert data.get("error", None) is None
        assert data.get("result") == input_value * 3

    run_test_coroutine(test_coroutine)


@pytest.mark.parametrize("coap_server", [{"action_clear_ms": 5}], indirect=True)
def test_action_clear_invocation(coap_server):
    """Completed Action invocations are removed from the CoAP server after a while."""

    @tornado.gen.coroutine
    def test_coroutine():
        invocation_sleep_secs = 0.1
        assert (invocation_sleep_secs * 1000) > coap_server.action_clear_ms
        response = yield _test_action_invoke(coap_server, invocation_sleep=invocation_sleep_secs)
        assert not response.code.is_successful()

    run_test_coroutine(test_coroutine)


def test_action_invoke_parallel(coap_server):
    """Actions exposed in a CoAP server can be invoked in parallel."""

    exposed_thing = next(coap_server.exposed_things)
    action_name = Faker().pystr()

    handler_futures = {}

    @tornado.gen.coroutine
    def handler(parameters):
        inp = parameters["input"]
        yield handler_futures[inp.get("future")]
        raise tornado.gen.Return(inp.get("number") * 3)

    exposed_thing.add_action(action_name, ActionFragmentDict({
        "input": {"type": "object"},
        "output": {"type": "number"}
    }), handler)

    href = _get_action_href(exposed_thing, action_name, coap_server)

    @tornado.gen.coroutine
    def invoke_action(coap_client):
        input_num = Faker().pyint()
        future_id = Faker().pystr()
        handler_futures[future_id] = tornado.concurrent.Future()

        payload = json.dumps({"input": {
            "number": input_num,
            "future": future_id
        }}).encode("utf-8")

        msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
        response = yield coap_client.request(msg).response
        assert response.code.is_successful()
        invocation_id = json.loads(response.payload).get("id")

        raise tornado.gen.Return({
            "number": input_num,
            "future": future_id,
            "id": invocation_id
        })

    def build_observe_request(coap_client, invocation):
        payload = json.dumps({"id": invocation["id"]}).encode("utf-8")
        msg = aiocoap.Message(code=aiocoap.Code.GET, payload=payload, uri=href, observe=0)
        return coap_client.request(msg)

    @tornado.gen.coroutine
    def test_coroutine():
        coap_client = yield aiocoap.Context.create_client_context()

        invocation_01, invocation_02 = yield [
            invoke_action(coap_client),
            invoke_action(coap_client)
        ]

        def unblock_01():
            handler_futures[invocation_01["future"]].set_result(True)

        def unblock_02():
            handler_futures[invocation_02["future"]].set_result(True)

        observe_req_01 = build_observe_request(coap_client, invocation_01)
        observe_req_02 = build_observe_request(coap_client, invocation_02)

        first_resp_01 = yield observe_req_01.response
        first_resp_02 = yield observe_req_02.response

        assert json.loads(first_resp_01.payload).get("done") is False
        assert json.loads(first_resp_02.payload).get("done") is False

        assert not handler_futures[invocation_01["future"]].done()
        assert not handler_futures[invocation_02["future"]].done()

        @tornado.gen.coroutine
        def wait_for_result(observe_req):
            res = None

            while not res or not res.get("done", False):
                res = yield _next_observation(observe_req)

            raise tornado.gen.Return(res)

        fut_result_01 = tornado.gen.convert_yielded(wait_for_result(observe_req_01))
        fut_result_02 = tornado.gen.convert_yielded(wait_for_result(observe_req_02))

        unblock_01()

        result_01 = yield fut_result_01

        assert result_01.get("done") is True
        assert result_01.get("id") == invocation_01.get("id")
        assert result_01.get("result") == invocation_01.get("number") * 3

        assert not fut_result_02.done()

        unblock_02()

        result_02 = yield fut_result_02

        assert result_02.get("done") is True
        assert result_02.get("id") == invocation_02.get("id")
        assert result_02.get("result") == invocation_02.get("number") * 3

        observe_req_01.observation.cancel()
        observe_req_02.observation.cancel()

    run_test_coroutine(test_coroutine)


def test_event_subscription(coap_server):
    """Event emissions can be observed in a CoAP server."""

    exposed_thing = next(coap_server.exposed_things)
    event_name = next(six.iterkeys(exposed_thing.thing.events))
    href = _get_event_href(exposed_thing, event_name, coap_server)

    emitted_values = [{
        "num": Faker().pyint(),
        "str": Faker().sentence()
    } for _ in range(5)]

    def emit_event():
        exposed_thing.emit_event(event_name, payload=emitted_values[0])

    def all_values_emitted():
        return len(emitted_values) == 0

    @tornado.gen.coroutine
    def test_coroutine():
        periodic_set = tornado.ioloop.PeriodicCallback(emit_event, 5)
        periodic_set.start()

        coap_client = yield aiocoap.Context.create_client_context()
        request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href, observe=0)
        request = coap_client.request(request_msg)
        first_response = yield request.response

        assert not first_response.payload

        while not all_values_emitted():
            payload = yield _next_observation(request)
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
        periodic_set.stop()

    run_test_coroutine(test_coroutine)
