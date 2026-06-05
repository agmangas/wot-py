#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

import pytest

from tests.protocols.helpers import (
    client_test_invoke_action_async,
    client_test_invoke_action_error_async,
    client_test_on_event_async,
    client_test_on_property_change_async,
    client_test_read_property_async,
    client_test_write_property_async,
)
from tests.protocols.mqtt.broker import BROKER_SKIP_REASON, is_test_broker_online
from wotpy.protocols.mqtt.client import MQTTClient

pytestmark = pytest.mark.skipif(
    is_test_broker_online() is False, reason=BROKER_SKIP_REASON
)


@pytest.mark.asyncio
async def test_read_property(mqtt_servient):
    """Property values may be retrieved using the MQTT binding client."""

    async for servient in mqtt_servient:
        await client_test_read_property_async(servient, MQTTClient)


@pytest.mark.asyncio
async def test_write_property(mqtt_servient):
    """Properties may be updated using the MQTT binding client."""

    async for servient in mqtt_servient:
        await client_test_write_property_async(servient, MQTTClient)


@pytest.mark.asyncio
async def test_invoke_action(mqtt_servient):
    """Actions may be invoked using the MQTT binding client."""

    async for servient in mqtt_servient:
        await client_test_invoke_action_async(servient, MQTTClient)


@pytest.mark.asyncio
async def test_invoke_action_error(mqtt_servient):
    """Errors raised by Actions are propagated propertly by the MQTT binding client."""

    async for servient in mqtt_servient:
        await client_test_invoke_action_error_async(servient, MQTTClient)


@pytest.mark.asyncio
async def test_on_property_change(mqtt_servient):
    """Property updates may be observed using the MQTT binding client."""

    async for servient in mqtt_servient:
        await client_test_on_property_change_async(servient, MQTTClient)


@pytest.mark.asyncio
async def test_on_event(mqtt_servient):
    """Event emissions may be observed using the MQTT binding client."""

    async for servient in mqtt_servient:
        await client_test_on_event_async(servient, MQTTClient)


@pytest.mark.skip(reason="ToDo: Implement this test")
def test_timeout_invoke_action(mqtt_servient):
    """Timeouts can be defined on Action invocations."""

    pass


@pytest.mark.skip(reason="ToDo: Implement this test")
def test_timeout_read_property(mqtt_servient):
    """Timeouts can be defined on Property reads."""

    pass


@pytest.mark.skip(reason="ToDo: Implement this test")
def test_timeout_write_property(mqtt_servient):
    """Timeouts can be defined on Property writes."""

    pass


@pytest.mark.skip(reason="ToDo: Implement this test")
def test_timeout_stop(mqtt_servient):
    """Attempting to stop an unresponsive connection does not result in an indefinite wait."""

    pass
