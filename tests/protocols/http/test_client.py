#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyPackageRequirements
import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.websocket
from faker import Faker

from tests.protocols.helpers import \
    client_test_on_property_change, \
    client_test_on_event, \
    client_test_read_property, \
    client_test_write_property
from wotpy.protocols.http.client import HTTPClient
from wotpy.td.description import ThingDescription


@pytest.mark.flaky(reruns=5)
def test_read_property(http_servient):
    """The HTTP client can read properties."""

    client_test_read_property(http_servient, HTTPClient)


@pytest.mark.flaky(reruns=5)
def test_write_property(http_servient):
    """The HTTP client can write properties."""

    client_test_write_property(http_servient, HTTPClient)


@pytest.mark.flaky(reruns=5)
def test_invoke_action(http_servient):
    """The HTTP client can invoke actions."""

    exposed_thing = next(http_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = HTTPClient()
        action_name = next(six.iterkeys(td.actions))
        input_value = Faker().pyint()

        @tornado.gen.coroutine
        def multiply_by_three(parameters):
            raise tornado.gen.Return(parameters.get("input") * 3)

        exposed_thing.set_action_handler(action_name, multiply_by_three)

        result = yield http_client.invoke_action(td, action_name, input_value, check_interval_ms=20)

        assert result == input_value * 3

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_event(http_servient):
    """The HTTP client can subscribe to event emissions."""

    client_test_on_event(http_servient, HTTPClient)


@pytest.mark.flaky(reruns=5)
def test_on_property_change(http_servient):
    """The HTTP client can subscribe to property updates."""

    client_test_on_property_change(http_servient, HTTPClient)
