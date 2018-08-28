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

    @tornado.gen.coroutine
    def test_coroutine():
        periodic_set = tornado.ioloop.PeriodicCallback(update_property, 5)
        periodic_set.start()

        coap_client = yield aiocoap.Context.create_client_context()
        request_msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href, observe=0)
        request = coap_client.request(request_msg)

        @tornado.gen.coroutine
        def get_next_observation():
            resp = yield request.observation.__aiter__().__anext__()
            val = json.loads(resp.payload).get("value")
            raise tornado.gen.Return(val)

        while True:
            value = yield get_next_observation()

            try:
                future_values.pop(future_values.index(value))
            except ValueError:
                pass

            if len(future_values) == 0:
                break

        request.observation.cancel()
        periodic_set.stop()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_action_invoke(coap_server):
    """Actions exposed in a CoAP server can be invoked and observed for their eventual results."""

    exposed_thing = next(coap_server.exposed_things)
    action_name = next(six.iterkeys(exposed_thing.thing.actions))
    href = _get_action_href(exposed_thing, action_name, coap_server)

    future_handler_block = tornado.concurrent.Future()

    # noinspection PyUnusedLocal
    @tornado.gen.coroutine
    def the_handler(parameters):
        yield future_handler_block
        raise tornado.gen.Return(parameters.get("input") * 3)

    exposed_thing.set_action_handler(action_name, the_handler)

    @tornado.gen.coroutine
    def test_coroutine():
        input_value = Faker().pyint()

        coap_client = yield aiocoap.Context.create_client_context()

        invoke_req_payload = json.dumps({"input": input_value}).encode("utf-8")
        invoke_msg = aiocoap.Message(code=aiocoap.Code.POST, payload=invoke_req_payload, uri=href)
        invoke_resp = yield coap_client.request(invoke_msg).response
        invocation_id = json.loads(invoke_resp.payload).get("invocation")

        observe_req_payload = json.dumps({"invocation": invocation_id}).encode("utf-8")
        observe_msg = aiocoap.Message(code=aiocoap.Code.GET, payload=observe_req_payload, uri=href, observe=0)
        observe_req = coap_client.request(observe_msg)

        first_observe_resp = yield observe_req.response

        assert json.loads(first_observe_resp.payload).get("done") is False

        def unblock_handler():
            future_handler_block.set_result(True)

        @tornado.gen.coroutine
        def get_next_observation():
            resp = yield observe_req.observation.__aiter__().__anext__()
            resp_payload = json.loads(resp.payload)
            raise tornado.gen.Return(resp_payload)

        tornado.ioloop.IOLoop.current().add_callback(unblock_handler)
        observation_payload = yield get_next_observation()

        assert observation_payload.get("done") is True
        assert observation_payload.get("result") == input_value * 3

        observe_req.observation.cancel()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
