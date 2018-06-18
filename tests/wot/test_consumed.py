#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.websocket
# noinspection PyPackageRequirements
from faker import Faker
from rx.concurrency import IOLoopScheduler
from tornado.concurrent import Future

from wotpy.td.description import ThingDescription
from wotpy.wot.consumed.thing import ConsumedThing


def test_read_property(websocket_servient):
    """A ConsumedThing is able to read properties."""

    servient = websocket_servient.pop("servient")
    exposed_thing = websocket_servient.pop("exposed_thing")
    td = ThingDescription.from_thing(exposed_thing.thing)
    consumed_thing = ConsumedThing(servient=servient, td=td)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(td.properties))

        result_exposed = yield exposed_thing.read_property(prop_name)
        result_consumed = yield consumed_thing.read_property(prop_name)

        assert result_consumed == result_exposed

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_write_property(websocket_servient):
    """A ConsumedThing is able to write properties."""

    servient = websocket_servient.pop("servient")
    exposed_thing = websocket_servient.pop("exposed_thing")
    td = ThingDescription.from_thing(exposed_thing.thing)
    consumed_thing = ConsumedThing(servient=servient, td=td)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(td.properties))

        val_01 = Faker().sentence()
        val_02 = Faker().sentence()

        yield exposed_thing.write_property(prop_name, val_01)
        value = yield exposed_thing.read_property(prop_name)

        assert value == val_01

        yield consumed_thing.write_property(prop_name, val_02)
        value = yield exposed_thing.read_property(prop_name)

        assert value == val_02

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_invoke_action(websocket_servient):
    """A ConsumedThing is able to invoke actions."""

    servient = websocket_servient.pop("servient")
    exposed_thing = websocket_servient.pop("exposed_thing")
    td = ThingDescription.from_thing(exposed_thing.thing)
    consumed_thing = ConsumedThing(servient=servient, td=td)

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = next(six.iterkeys(td.actions))

        arg_a = Faker().sentence()
        arg_b = Faker().sentence()

        result = yield consumed_thing.invoke_action(action_name, arg_a=arg_a, arg_b=arg_b)
        result_expected = arg_a + arg_b

        assert result == result_expected

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_on_event(websocket_servient):
    """A ConsumedThing is able to observe events."""

    servient = websocket_servient.pop("servient")
    exposed_thing = websocket_servient.pop("exposed_thing")
    td = ThingDescription.from_thing(exposed_thing.thing)
    consumed_thing = ConsumedThing(servient=servient, td=td)

    @tornado.gen.coroutine
    def test_coroutine():
        event_name = next(six.iterkeys(td.events))

        future_conn = Future()
        future_event = Future()

        def on_next(ev):
            if not future_conn.done():
                future_conn.set_result(True)
            else:
                future_event.set_result(ev.data)

        observable = consumed_thing.on_event(event_name)
        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        while not future_conn.done():
            exposed_thing.emit_event(event_name, Faker().sentence())
            yield tornado.gen.sleep(0.1)

        payload = Faker().sentence()
        exposed_thing.emit_event(event_name, payload)

        yield future_event

        assert future_event.result() == payload

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_on_property_change(websocket_servient):
    """A ConsumedThing is able to observe property updates."""

    servient = websocket_servient.pop("servient")
    exposed_thing = websocket_servient.pop("exposed_thing")
    td = ThingDescription.from_thing(exposed_thing.thing)
    consumed_thing = ConsumedThing(servient=servient, td=td)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(td.properties))

        future_conn = Future()
        future_change = Future()

        def on_next(ev):
            if not future_conn.done():
                future_conn.set_result(True)
            else:
                future_change.set_result(ev.data.value)

        observable = consumed_thing.on_property_change(prop_name)
        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        while not future_conn.done():
            yield exposed_thing.write_property(prop_name, Faker().sentence())
            yield tornado.gen.sleep(0.1)

        prop_value = Faker().sentence()
        yield exposed_thing.write_property(prop_name, prop_value)

        yield future_change

        assert future_change.result() == prop_value

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
