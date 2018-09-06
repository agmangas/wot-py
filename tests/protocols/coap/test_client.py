#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.websocket
from faker import Faker

from wotpy.protocols.coap.client import CoAPClient
from wotpy.td.description import ThingDescription


@pytest.mark.flaky(reruns=5)
def test_read_property(coap_servient):
    """The CoAP client can read properties."""

    exposed_thing = next(coap_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        coap_client = CoAPClient()
        prop_name = next(six.iterkeys(td.properties))
        prop_value = Faker().sentence()

        coap_prop_value = yield coap_client.read_property(td, prop_name)
        assert coap_prop_value != prop_value

        yield exposed_thing.properties[prop_name].write(prop_value)

        coap_prop_value = yield coap_client.read_property(td, prop_name)
        assert coap_prop_value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_write_property(coap_servient):
    """The CoAP client can write properties."""

    exposed_thing = next(coap_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        coap_client = CoAPClient()
        prop_name = next(six.iterkeys(td.properties))
        prop_value = Faker().sentence()

        prev_value = yield exposed_thing.properties[prop_name].read()
        assert prev_value != prop_value

        yield coap_client.write_property(td, prop_name, prop_value)

        curr_value = yield exposed_thing.properties[prop_name].read()
        assert curr_value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_invoke_action(coap_servient):
    """The CoAP client can invoke actions."""

    exposed_thing = next(coap_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        coap_client = CoAPClient()
        action_name = next(six.iterkeys(td.actions))
        input_value = Faker().pyint()

        @tornado.gen.coroutine
        def double(parameters):
            yield tornado.gen.sleep(0.1)
            raise tornado.gen.Return(parameters.get("input") * 2)

        exposed_thing.set_action_handler(action_name, double)

        result = yield coap_client.invoke_action(td, action_name, input_value)

        assert result == input_value * 2

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
