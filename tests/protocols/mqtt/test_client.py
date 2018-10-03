#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
from faker import Faker

from tests.protocols.helpers import \
    client_test_on_property_change, \
    client_test_on_event, \
    client_test_read_property
from tests.protocols.mqtt.broker import is_test_broker_online, BROKER_SKIP_REASON
from wotpy.protocols.mqtt.client import MQTTClient
from wotpy.td.description import ThingDescription

pytestmark = pytest.mark.skipif(is_test_broker_online() is False, reason=BROKER_SKIP_REASON)


def test_read_property(mqtt_servient):
    """Property values may be retrieved using the MQTT binding client."""

    client_test_read_property(mqtt_servient, MQTTClient)


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

    client_test_on_property_change(mqtt_servient, MQTTClient)


def test_on_event(mqtt_servient):
    """Event emissions may be observed using the MQTT binding client."""

    client_test_on_event(mqtt_servient, MQTTClient)
