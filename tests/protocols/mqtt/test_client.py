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
from tests.utils import run_test_coroutine, DEFAULT_TIMEOUT_SECS
from wotpy.protocols.exceptions import ClientRequestTimeout
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


# noinspection PyUnusedLocal
def _effect_dummy(*args, **kwargs):
    """Coroutine mock side effect that does nothing and returns a Mock."""

    @tornado.gen.coroutine
    def _coro():
        yield tornado.gen.moment
        raise tornado.gen.Return(MagicMock())

    return _coro()


# noinspection PyUnusedLocal
def _effect_raise_timeout(*args, **kwargs):
    """Coroutine mock side effect that raises a timeout error."""

    @tornado.gen.coroutine
    def _coro():
        yield tornado.gen.moment
        raise asyncio.TimeoutError

    return _coro()


def _build_effect_sleep(sleep_secs):
    """Factory function to build coroutine mock side effects to sleep a fixed amount of time."""

    # noinspection PyUnusedLocal
    def _effect_wait(*args, **kwargs):
        @tornado.gen.coroutine
        def _coro():
            yield tornado.gen.sleep(sleep_secs)
            raise asyncio.TimeoutError

        return _coro()

    return _effect_wait


def _build_hbmqtt_mock(side_effect_deliver_message):
    """Returns a mock of the HBMQTT Client class."""

    mock_client = MagicMock()
    mock_client.connect.side_effect = _effect_dummy
    mock_client.deliver_message.side_effect = side_effect_deliver_message
    mock_client.disconnect.side_effect = _effect_dummy
    mock_client.subscribe.side_effect = _effect_dummy
    mock_client.publish.side_effect = _effect_dummy

    mock_cls = MagicMock()
    mock_cls.return_value = mock_client

    return mock_cls


def test_timeout_invoke_action(mqtt_servient):
    """Timeouts can be defined on Action invocations."""

    exposed_thing = next(mqtt_servient.exposed_things)
    action_name = next(six.iterkeys(exposed_thing.actions))
    td = ThingDescription.from_thing(exposed_thing.thing)
    mqtt_mock = _build_hbmqtt_mock(_effect_raise_timeout)

    timeout = random.random()

    @tornado.gen.coroutine
    def test_coroutine():
        with patch('wotpy.protocols.mqtt.client.hbmqtt.client.MQTTClient', new=mqtt_mock):
            mqtt_client = MQTTClient()

            with pytest.raises(ClientRequestTimeout):
                yield mqtt_client.invoke_action(td, action_name, Faker().pystr(), timeout=timeout)

    run_test_coroutine(test_coroutine)


def test_timeout_read_property(mqtt_servient):
    """Timeouts can be defined on Property reads."""

    exposed_thing = next(mqtt_servient.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.properties))
    td = ThingDescription.from_thing(exposed_thing.thing)
    mqtt_mock = _build_hbmqtt_mock(_effect_raise_timeout)

    timeout = random.random()

    @tornado.gen.coroutine
    def test_coroutine():
        with patch('wotpy.protocols.mqtt.client.hbmqtt.client.MQTTClient', new=mqtt_mock):
            mqtt_client = MQTTClient()

            with pytest.raises(ClientRequestTimeout):
                yield mqtt_client.read_property(td, prop_name, timeout=timeout)

    run_test_coroutine(test_coroutine)


def test_timeout_write_property(mqtt_servient):
    """Timeouts can be defined on Property writes."""

    exposed_thing = next(mqtt_servient.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.properties))
    td = ThingDescription.from_thing(exposed_thing.thing)
    mqtt_mock = _build_hbmqtt_mock(_effect_raise_timeout)

    timeout = random.random()

    @tornado.gen.coroutine
    def test_coroutine():
        with patch('wotpy.protocols.mqtt.client.hbmqtt.client.MQTTClient', new=mqtt_mock):
            mqtt_client = MQTTClient()

            with pytest.raises(ClientRequestTimeout):
                yield mqtt_client.write_property(td, prop_name, Faker().pystr(), timeout=timeout)

    run_test_coroutine(test_coroutine)


def test_stop_timeout(mqtt_servient):
    """Attempting to stop an unresponsive connection does not result in an indefinite wait."""

    exposed_thing = next(mqtt_servient.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.properties))
    td = ThingDescription.from_thing(exposed_thing.thing)

    timeout = random.random()

    assert (timeout * 3) < DEFAULT_TIMEOUT_SECS

    mqtt_mock = _build_hbmqtt_mock(_build_effect_sleep(DEFAULT_TIMEOUT_SECS * 10))

    @tornado.gen.coroutine
    def test_coroutine():
        with patch('wotpy.protocols.mqtt.client.hbmqtt.client.MQTTClient', new=mqtt_mock):
            mqtt_client = MQTTClient(stop_loop_timeout_secs=timeout)

            with pytest.raises(ClientRequestTimeout):
                yield mqtt_client.read_property(td, prop_name, timeout=timeout)

    run_test_coroutine(test_coroutine)
