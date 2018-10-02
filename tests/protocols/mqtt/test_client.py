#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import six
import tornado.gen
import tornado.ioloop
from faker import Faker

from tests.protocols.mqtt.broker import is_test_broker_online, BROKER_SKIP_REASON
from wotpy.protocols.mqtt.client import MQTTClient
from wotpy.td.description import ThingDescription

pytestmark = pytest.mark.skipif(is_test_broker_online() is False, reason=BROKER_SKIP_REASON)


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
