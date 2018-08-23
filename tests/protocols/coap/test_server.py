#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random

import aiocoap
import pytest
import six
import tornado.gen
import tornado.ioloop
from faker import Faker

from wotpy.protocols.coap.server import CoAPServer


def _get_property_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property read/write href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("127.0.0.1", prop)
    return next(item.href for item in prop_forms if item.rel is None)


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
            request = aiocoap.Message(code=aiocoap.Code.GET, uri=ping_uri)
            response = yield coap_client.request(request).response
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
        request = aiocoap.Message(code=aiocoap.Code.GET, uri=href)
        response = yield coap_client.request(request).response

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
        request = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
        response = yield coap_client.request(request).response

        assert response.code.is_successful()
        assert (yield exposed_thing.properties[prop_name].read()) == value_new

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
