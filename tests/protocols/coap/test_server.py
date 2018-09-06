#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import json
import random

import aiocoap
import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
from faker import Faker

from wotpy.protocols.coap.server import CoAPServer
from wotpy.protocols.enums import InteractionVerbs
from wotpy.wot.dictionaries.interaction import ActionFragment


def _get_property_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property read/write href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("127.0.0.1", prop)
    return next(item.href for item in prop_forms if item.rel is None)


def _get_property_observe_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property subscription href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("127.0.0.1", prop)
    return next(item.href for item in prop_forms if item.rel == InteractionVerbs.OBSERVE_PROPERTY)


def _get_action_href(exp_thing, action_name, server):
    """Helper function to retrieve the Action invocation href."""

    action = exp_thing.thing.actions[action_name]
    action_forms = server.build_forms("127.0.0.1", action)
    return next(item.href for item in action_forms)


def _get_event_href(exp_thing, event_name, server):
    """Helper function to retrieve the Event subscription href."""

    event = exp_thing.thing.events[event_name]
    event_forms = server.build_forms("127.0.0.1", event)
    return next(item.href for item in event_forms)


@tornado.gen.coroutine
def _next_observation(request):
    """Yields the next observation for the given CoAP request."""

    resp = yield request.observation.__aiter__().__anext__()
    val = json.loads(resp.payload)
    raise tornado.gen.Return(val)


@pytest.mark.flaky(reruns=5)
def test_start_stop():
    """The CoAP server can be started and stopped."""

    coap_port = random.randint(20000, 40000)
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

        coap_server.start()
        yield tornado.gen.sleep(0)

        assert (yield ping())
        assert (yield ping())

        coap_server.stop()
        yield tornado.gen.sleep(0)

        assert not (yield ping())

        coap_server.stop()
        coap_server.start()
        coap_server.start()
        yield tornado.gen.sleep(0)

        assert (yield ping())

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
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

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
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
        request_msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
        response = yield coap_client.request(request_msg).response

        assert response.code.is_successful()
        assert (yield exposed_thing.properties[prop_name].read()) == value_new

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
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

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_action_invoke(coap_server):
    """Actions exposed in a CoAP server can be invoked and observed for their eventual results."""

    exposed_thing = next(coap_server.exposed_things)
    action_name = Faker().pystr()

    handler_futures = {}

    @tornado.gen.coroutine
    def handler(parameters):
        inp = parameters["input"]
        yield handler_futures[inp.get("future")]
        raise tornado.gen.Return(inp.get("number") * 3)

    exposed_thing.add_action(action_name, ActionFragment({
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
        invocation_id = json.loads(response.payload).get("invocation")

        raise tornado.gen.Return({
            "number": input_num,
            "future": future_id,
            "id": invocation_id
        })

    def build_observe_request(coap_client, invocation):
        payload = json.dumps({"invocation": invocation["id"]}).encode("utf-8")
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

        fut_result_01 = _next_observation(observe_req_01)
        fut_result_02 = _next_observation(observe_req_02)

        unblock_01()

        result_01 = yield fut_result_01

        assert result_01.get("done") is True
        assert result_01.get("invocation") == invocation_01.get("id")
        assert result_01.get("result") == invocation_01.get("number") * 3

        # noinspection PyUnresolvedReferences
        assert not fut_result_02.done()

        unblock_02()

        result_02 = yield fut_result_02

        assert result_02.get("done") is True
        assert result_02.get("invocation") == invocation_02.get("id")
        assert result_02.get("result") == invocation_02.get("number") * 3

        observe_req_01.observation.cancel()
        observe_req_02.observation.cancel()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
@pytest.mark.parametrize("coap_server", [{"action_clear_ms": 5}], indirect=True)
def test_action_clear(coap_server):
    """Completed Action invocations are removed from the CoAP server after a while."""

    exposed_thing = next(coap_server.exposed_things)
    action_name = next(six.iterkeys(exposed_thing.thing.actions))
    href = _get_action_href(exposed_thing, action_name, coap_server)

    @tornado.gen.coroutine
    def test_coroutine():
        coap_client = yield aiocoap.Context.create_client_context()

        payload = json.dumps({"input": Faker().pyint()}).encode("utf-8")
        msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
        response = yield coap_client.request(msg).response
        invocation_id = json.loads(response.payload).get("invocation")

        assert invocation_id

        yield tornado.gen.sleep(0.01)

        obsv_payload = json.dumps({"invocation": invocation_id}).encode("utf-8")
        obsv_msg = aiocoap.Message(code=aiocoap.Code.GET, payload=obsv_payload, uri=href, observe=0)
        obsv_response = yield coap_client.request(obsv_msg).response

        assert not obsv_response.code.is_successful()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_event_subscription(coap_server):
    """Event emissions can be observed in a CoAP server."""

    exposed_thing = next(coap_server.exposed_things)
    event_name = next(six.iterkeys(exposed_thing.thing.events))
    href = _get_event_href(exposed_thing, event_name, coap_server)

    emitted_values = [{"num": Faker().pyint(), "str": Faker().sentence()} for _ in range(5)]

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

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
