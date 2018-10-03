#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest

from tests.protocols.helpers import \
    client_test_on_property_change, \
    client_test_on_event, \
    client_test_read_property, \
    client_test_write_property, \
    client_test_invoke_action, \
    client_test_invoke_action_error
from tests.protocols.mqtt.broker import is_test_broker_online, BROKER_SKIP_REASON
from wotpy.protocols.mqtt.client import MQTTClient

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
