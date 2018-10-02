#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
from faker import Faker
from rx.concurrency import IOLoopScheduler

from tests.protocols.mqtt.broker import is_test_broker_online, BROKER_SKIP_REASON
from wotpy.protocols.mqtt.client import MQTTClient
from wotpy.td.description import ThingDescription

pytestmark = pytest.mark.skipif(is_test_broker_online() is False, reason=BROKER_SKIP_REASON)


def test_read_property(mqtt_servient):
    """Property values may be retrieved using the MQTT binding client."""

    exposed_thing = next(mqtt_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        mqtt_client = MQTTClient()
        prop_name = next(six.iterkeys(td.properties))
        prop_value = Faker().sentence()

        coap_prop_value = yield mqtt_client.read_property(td, prop_name)
        assert coap_prop_value != prop_value

        yield exposed_thing.properties[prop_name].write(prop_value)

        coap_prop_value = yield mqtt_client.read_property(td, prop_name)
        assert coap_prop_value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_write_property(mqtt_servient):
    """Properties may be updated using the MQTT binding client."""

    exposed_thing = next(mqtt_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        mqtt_client = MQTTClient()
        prop_name = next(six.iterkeys(td.properties))
        prop_value = Faker().sentence()

        prev_value = yield exposed_thing.properties[prop_name].read()
        assert prev_value != prop_value

        yield mqtt_client.write_property(td, prop_name, prop_value)

        curr_value = None

        while curr_value != prop_value:
            curr_value = yield exposed_thing.properties[prop_name].read()
            yield None

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_invoke_action(mqtt_servient):
    """Actions may be invoked using the MQTT binding client."""

    exposed_thing = next(mqtt_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        mqtt_client = MQTTClient()
        action_name = next(six.iterkeys(td.actions))
        input_value = Faker().pyint()

        result = yield mqtt_client.invoke_action(td, action_name, input_value)

        assert result == input_value * 2

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_invoke_action_error(mqtt_servient):
    """Errors raised by Actions are propagated propertly by the MQTT binding client."""

    exposed_thing = next(mqtt_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        mqtt_client = MQTTClient()
        action_name = next(six.iterkeys(td.actions))
        input_value = Faker().pyint()
        err_message = Faker().sentence()

        # noinspection PyUnusedLocal
        def handler_err(parameters):
            raise ValueError(err_message)

        exposed_thing.set_action_handler(action_name, handler_err)

        with pytest.raises(Exception) as ex:
            yield mqtt_client.invoke_action(td, action_name, input_value)
            assert err_message in str(ex)

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_on_property_change(mqtt_servient):
    """Property updates may be observed using the MQTT binding client."""

    exposed_thing = next(mqtt_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        mqtt_client = MQTTClient()
        property_name = next(six.iterkeys(td.properties))

        values = [Faker().sentence() for _ in range(10)]
        values_observed = {value: tornado.concurrent.Future() for value in values}

        @tornado.gen.coroutine
        def write_next():
            try:
                next_value = next(val for val, fut in six.iteritems(values_observed) if not fut.done())
                yield exposed_thing.properties[property_name].write(next_value)
            except StopIteration:
                pass

        def on_next(ev):
            prop_value = ev.data.value
            if prop_value in values_observed and not values_observed[prop_value].done():
                values_observed[prop_value].set_result(True)

        observable = mqtt_client.on_property_change(td, property_name)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        periodic_emit = tornado.ioloop.PeriodicCallback(write_next, 10)
        periodic_emit.start()

        yield list(values_observed.values())

        periodic_emit.stop()
        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_on_event(mqtt_servient):
    """Event emissions may be observed using the MQTT binding client."""

    exposed_thing = next(mqtt_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        coap_client = MQTTClient()
        event_name = next(six.iterkeys(td.events))

        payloads = [uuid.uuid4().hex for _ in range(10)]
        future_payloads = {key: tornado.concurrent.Future() for key in payloads}

        @tornado.gen.coroutine
        def emit_next():
            next_value = next(val for val, fut in six.iteritems(future_payloads) if not fut.done())
            exposed_thing.events[event_name].emit(next_value)

        def on_next(ev):
            if ev.data in future_payloads and not future_payloads[ev.data].done():
                future_payloads[ev.data].set_result(True)

        observable = coap_client.on_event(td, event_name)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        periodic_emit = tornado.ioloop.PeriodicCallback(emit_next, 10)
        periodic_emit.start()

        yield list(future_payloads.values())

        periodic_emit.stop()
        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
