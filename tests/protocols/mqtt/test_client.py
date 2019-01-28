#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import random

import pytest
import six
import tornado.gen
from faker import Faker
from mock import MagicMock, patch

from tests.protocols.helpers import \
    client_test_on_property_change, \
    client_test_on_event, \
    client_test_read_property, \
    client_test_write_property, \
    client_test_invoke_action, \
    client_test_invoke_action_error
from tests.protocols.mqtt.broker import is_test_broker_online, BROKER_SKIP_REASON
from tests.utils import run_test_coroutine
from wotpy.protocols.mqtt.client import MQTTClient
from wotpy.wot.td import ThingDescription

pytestmark = pytest.mark.skipif(is_test_broker_online() is False, reason=BROKER_SKIP_REASON)


def test_read_property(mqtt_servient):
    """Property values may be retrieved using the MQTT binding client."""

    client_test_read_property(mqtt_servient, MQTTClient)


def test_write_property(mqtt_servient):
    """Properties may be updated using the MQTT binding client."""

    client_test_write_property(mqtt_servient, MQTTClient)


def test_invoke_action(mqtt_servient):
    """Actions may be invoked using the MQTT binding client."""

    client_test_invoke_action(mqtt_servient, MQTTClient)


def test_invoke_action_error(mqtt_servient):
    """Errors raised by Actions are propagated propertly by the MQTT binding client."""

    client_test_invoke_action_error(mqtt_servient, MQTTClient)


def test_on_property_change(mqtt_servient):
    """Property updates may be observed using the MQTT binding client."""

    client_test_on_property_change(mqtt_servient, MQTTClient)


def test_on_event(mqtt_servient):
    """Event emissions may be observed using the MQTT binding client."""

    client_test_on_event(mqtt_servient, MQTTClient)


def _hbmqtt_mock():
    """Returns a mock of the HBMQTT Client class."""

    # noinspection PyUnusedLocal
    def dummy_effect(*args, **kwargs):
        @tornado.gen.coroutine
        def _coro():
            yield tornado.gen.moment
            raise tornado.gen.Return(MagicMock())

        return _coro()

    # noinspection PyUnusedLocal
    def raise_timeout_effect(*args, **kwargs):
        @tornado.gen.coroutine
        def _coro():
            yield tornado.gen.moment
            raise asyncio.TimeoutError

        return _coro()

    mock_client = MagicMock()
    mock_client.connect.side_effect = dummy_effect
    mock_client.deliver_message.side_effect = raise_timeout_effect
    mock_client.disconnect.side_effect = dummy_effect
    mock_client.subscribe.side_effect = dummy_effect
    mock_client.publish.side_effect = dummy_effect

    mock_cls = MagicMock()
    mock_cls.return_value = mock_client

    return mock_cls


def test_timeout_invoke_action(mqtt_servient):
    """Timeouts can be defined on Action invocations."""

    exposed_thing = next(mqtt_servient.exposed_things)
    action_name = next(six.iterkeys(exposed_thing.actions))
    td = ThingDescription.from_thing(exposed_thing.thing)

    timeout = random.random()

    @tornado.gen.coroutine
    def test_coroutine():
        with patch('wotpy.protocols.mqtt.client.hbmqtt.client.MQTTClient', new=_hbmqtt_mock()):
            mqtt_client = MQTTClient()

            with pytest.raises(asyncio.TimeoutError):
                yield mqtt_client.invoke_action(td, action_name, Faker().pystr(), timeout=timeout)

    run_test_coroutine(test_coroutine)


def test_timeout_read_property(mqtt_servient):
    """Timeouts can be defined on Property reads."""

    exposed_thing = next(mqtt_servient.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.properties))
    td = ThingDescription.from_thing(exposed_thing.thing)

    timeout = random.random()

    @tornado.gen.coroutine
    def test_coroutine():
        with patch('wotpy.protocols.mqtt.client.hbmqtt.client.MQTTClient', new=_hbmqtt_mock()):
            mqtt_client = MQTTClient()

            with pytest.raises(asyncio.TimeoutError):
                yield mqtt_client.read_property(td, prop_name, timeout=timeout)

    run_test_coroutine(test_coroutine)


def test_timeout_write_property(mqtt_servient):
    """Timeouts can be defined on Property writes."""

    exposed_thing = next(mqtt_servient.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.properties))
    td = ThingDescription.from_thing(exposed_thing.thing)

    timeout = random.random()

    @tornado.gen.coroutine
    def test_coroutine():
        with patch('wotpy.protocols.mqtt.client.hbmqtt.client.MQTTClient', new=_hbmqtt_mock()):
            mqtt_client = MQTTClient()

            with pytest.raises(asyncio.TimeoutError):
                yield mqtt_client.write_property(td, prop_name, Faker().pystr(), timeout=timeout)

    run_test_coroutine(test_coroutine)
