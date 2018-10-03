#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
from faker import Faker
from rx.concurrency import IOLoopScheduler

from wotpy.td.description import ThingDescription
from wotpy.wot.dictionaries.interaction import PropertyFragment, EventFragment


def client_test_on_property_change(servient, protocol_client_cls):
    """Helper function to test observation of Property updates on bindings clients."""

    exposed_thing = next(servient.exposed_things)

    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(prop_name, PropertyFragment({
        "type": "string",
        "writable": True,
        "observable": True
    }), value=Faker().sentence())

    servient.refresh_forms()

    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        protocol_client = protocol_client_cls()

        values = [Faker().sentence() for _ in range(10)]
        values_observed = {value: tornado.concurrent.Future() for value in values}

        @tornado.gen.coroutine
        def write_next():
            try:
                next_value = next(val for val, fut in six.iteritems(values_observed) if not fut.done())
                yield exposed_thing.properties[prop_name].write(next_value)
            except StopIteration:
                pass

        def on_next(ev):
            prop_value = ev.data.value
            if prop_value in values_observed and not values_observed[prop_value].done():
                values_observed[prop_value].set_result(True)

        observable = protocol_client.on_property_change(td, prop_name)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        periodic_emit = tornado.ioloop.PeriodicCallback(write_next, 10)
        periodic_emit.start()

        yield list(values_observed.values())

        periodic_emit.stop()
        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def client_test_on_event(servient, protocol_client_cls):
    """Helper function to test observation of Events on bindings clients."""

    exposed_thing = next(servient.exposed_things)

    event_name = uuid.uuid4().hex

    exposed_thing.add_event(event_name, EventFragment({
        "type": "number"
    }))

    servient.refresh_forms()

    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        protocol_client = protocol_client_cls()

        payloads = [Faker().pyint() for _ in range(10)]
        future_payloads = {key: tornado.concurrent.Future() for key in payloads}

        @tornado.gen.coroutine
        def emit_next():
            next_value = next(val for val, fut in six.iteritems(future_payloads) if not fut.done())
            exposed_thing.events[event_name].emit(next_value)

        def on_next(ev):
            if ev.data in future_payloads and not future_payloads[ev.data].done():
                future_payloads[ev.data].set_result(True)

        observable = protocol_client.on_event(td, event_name)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        periodic_emit = tornado.ioloop.PeriodicCallback(emit_next, 10)
        periodic_emit.start()

        yield list(future_payloads.values())

        periodic_emit.stop()
        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def client_test_read_property(servient, protocol_client_cls):
    """Helper function to test Property reads on bindings clients."""

    exposed_thing = next(servient.exposed_things)

    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(prop_name, PropertyFragment({
        "type": "string",
        "writable": True,
        "observable": True
    }), value=Faker().sentence())

    servient.refresh_forms()

    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        protocol_client = protocol_client_cls()
        prop_value = Faker().sentence()

        curr_prop_value = yield protocol_client.read_property(td, prop_name)
        assert curr_prop_value != prop_value

        yield exposed_thing.properties[prop_name].write(prop_value)

        curr_prop_value = yield protocol_client.read_property(td, prop_name)
        assert curr_prop_value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def client_test_write_property(servient, protocol_client_cls):
    """Helper function to test Property writes on bindings clients."""

    exposed_thing = next(servient.exposed_things)

    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(prop_name, PropertyFragment({
        "type": "string",
        "writable": True,
        "observable": True
    }), value=Faker().sentence())

    servient.refresh_forms()

    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        protocol_client = protocol_client_cls()
        prop_value = Faker().sentence()

        prev_value = yield exposed_thing.properties[prop_name].read()
        assert prev_value != prop_value

        yield protocol_client.write_property(td, prop_name, prop_value)

        curr_value = yield exposed_thing.properties[prop_name].read()
        assert curr_value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
