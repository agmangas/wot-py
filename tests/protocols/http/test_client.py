#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

# noinspection PyPackageRequirements
import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.websocket
from faker import Faker
from rx.concurrency import IOLoopScheduler
from tornado.concurrent import Future

from wotpy.protocols.http.client import HTTPClient
from wotpy.td.description import ThingDescription


@pytest.mark.flaky(reruns=5)
def test_read_property(http_servient):
    """The HTTP client can read properties."""

    exposed_thing = next(http_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = HTTPClient()
        prop_name = next(six.iterkeys(td.properties))
        prop_value = Faker().sentence()

        http_prop_value = yield http_client.read_property(td, prop_name)
        assert http_prop_value != prop_value

        yield exposed_thing.properties[prop_name].write(prop_value)

        http_prop_value = yield http_client.read_property(td, prop_name)
        assert http_prop_value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_write_property(http_servient):
    """The HTTP client can write properties."""

    exposed_thing = next(http_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = HTTPClient()
        prop_name = next(six.iterkeys(td.properties))
        prop_value = Faker().sentence()

        prev_value = yield exposed_thing.properties[prop_name].read()
        assert prev_value != prop_value

        yield http_client.write_property(td, prop_name, prop_value)

        curr_value = yield exposed_thing.properties[prop_name].read()
        assert curr_value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


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

    exposed_thing = next(http_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = HTTPClient()

        event_name = next(six.iterkeys(td.events))

        observable = http_client.on_event(td, event_name)

        payloads = [uuid.uuid4().hex for _ in range(10)]
        future_payloads = {key: Future() for key in payloads}

        @tornado.gen.coroutine
        def emit_next_event():
            next_value = next(val for val, fut in six.iteritems(future_payloads) if not fut.done())
            exposed_thing.events[event_name].emit(next_value)

        def on_next(ev):
            if ev.data in future_payloads and not future_payloads[ev.data].done():
                future_payloads[ev.data].set_result(True)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        periodic_emit = tornado.ioloop.PeriodicCallback(emit_next_event, 10)
        periodic_emit.start()

        yield list(future_payloads.values())

        periodic_emit.stop()
        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_property_change(http_servient):
    """The HTTP client can subscribe to property updates."""

    exposed_thing = next(http_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = HTTPClient()

        property_name = next(six.iterkeys(td.properties))

        observable = http_client.on_property_change(td, property_name)

        values = [Faker().sentence() for _ in range(10)]
        future_values = {value: Future() for value in values}

        @tornado.gen.coroutine
        def write_next_value():
            next_value = next(val for val, fut in six.iteritems(future_values) if not fut.done())
            yield exposed_thing.properties[property_name].write(next_value)

        def on_next(ev):
            prop_value = ev.data.value
            if prop_value in future_values and not future_values[prop_value].done():
                future_values[prop_value].set_result(True)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        periodic_emit = tornado.ioloop.PeriodicCallback(write_next_value, 10)
        periodic_emit.start()

        yield list(future_values.values())

        periodic_emit.stop()
        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
