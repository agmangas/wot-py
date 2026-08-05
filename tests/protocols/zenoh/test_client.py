#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 National Technical University of Athens
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

import asyncio
import random
import time

import pytest
from faker import Faker
from unittest.mock import MagicMock, patch

from tests.protocols.helpers import \
    client_test_on_property_change, \
    client_test_on_event, \
    client_test_read_property, \
    client_test_write_property, \
    client_test_invoke_action, \
    client_test_invoke_action_error
from tests.protocols.zenoh.router import is_test_router_online, ROUTER_SKIP_REASON
from tests.utils import run_test_coroutine, DEFAULT_TIMEOUT_SECS
from wotpy.protocols.exceptions import ClientRequestTimeout
from wotpy.protocols.zenoh.client import ZenohClient
from wotpy.wot.td import ThingDescription

pytestmark = pytest.mark.skipif(asyncio.run(is_test_router_online()) is False, reason=ROUTER_SKIP_REASON)


@pytest.mark.asyncio
async def test_read_property(zenoh_servient):
    """Property values may be retrieved using the Zenoh binding client."""

    await client_test_read_property(zenoh_servient, ZenohClient)


@pytest.mark.asyncio
async def test_write_property(zenoh_servient):
    """Properties may be updated using the Zenoh binding client."""

    await client_test_write_property(zenoh_servient, ZenohClient)


@pytest.mark.asyncio
async def test_invoke_action(zenoh_servient):
    """Actions may be invoked using the Zenoh binding client."""

    await client_test_invoke_action(zenoh_servient, ZenohClient)


@pytest.mark.asyncio
async def test_invoke_action_error(zenoh_servient):
    """Errors raised by Actions are propagated propertly by the Zenoh binding client."""

    await client_test_invoke_action_error(zenoh_servient, ZenohClient)


@pytest.mark.asyncio
async def test_on_property_change(zenoh_servient):
    """Property updates may be observed using the Zenoh binding client."""

    await client_test_on_property_change(zenoh_servient, ZenohClient)


@pytest.mark.asyncio
async def test_on_event(zenoh_servient):
    """Event emissions may be observed using the Zenoh binding client."""

    await client_test_on_event(zenoh_servient, ZenohClient)


def _effect_dummy(*args, **kwargs):
    """Coroutine mock side effect that does nothing and returns a Mock."""

    def _coro():
        time.sleep(0)
        return MagicMock()

    return _coro()


def _build_zenoh_mock():
    """Returns a mock of the Zenoh Session class."""

    mock_session = MagicMock()
    mock_session.connect.side_effect = _effect_dummy
    mock_session.close.side_effect = _effect_dummy
    mock_session.declare_subscriber.side_effect = _effect_dummy
    mock_session.put.side_effect = _effect_dummy

    mock_cls = MagicMock()
    mock_cls.return_value = mock_session

    return mock_cls


@pytest.mark.asyncio
async def test_timeout_invoke_action(zenoh_servient):
    """Timeouts can be defined on Action invocations."""

    exposed_thing = next(zenoh_servient.exposed_things)
    action_name = next(iter(exposed_thing.actions.keys()))
    td = ThingDescription.from_thing(exposed_thing.thing)
    zenoh_mock = _build_zenoh_mock()

    timeout = random.random()

    async def test_coroutine():
        with patch('wotpy.protocols.zenoh.client.zenoh.open', new=zenoh_mock):
            zenoh_client = ZenohClient()

            with pytest.raises(ClientRequestTimeout):
                await zenoh_client.invoke_action(td, action_name, Faker().pystr(), timeout=timeout)

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_timeout_read_property(zenoh_servient):
    """Timeouts can be defined on Property reads."""

    exposed_thing = next(zenoh_servient.exposed_things)
    prop_name = next(iter(exposed_thing.properties.keys()))
    td = ThingDescription.from_thing(exposed_thing.thing)
    zenoh_mock = _build_zenoh_mock()

    timeout = random.random()

    async def test_coroutine():
        with patch('wotpy.protocols.zenoh.client.zenoh.open', new=zenoh_mock):
            zenoh_client = ZenohClient()

            with pytest.raises(ClientRequestTimeout):
                await zenoh_client.read_property(td, prop_name, timeout=timeout)

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_timeout_write_property(zenoh_servient):
    """Timeouts can be defined on Property writes."""

    exposed_thing = next(zenoh_servient.exposed_things)
    prop_name = next(iter(exposed_thing.properties.keys()))
    td = ThingDescription.from_thing(exposed_thing.thing)
    zenoh_mock = _build_zenoh_mock()

    timeout = random.random()

    async def test_coroutine():
        with patch('wotpy.protocols.zenoh.client.zenoh.open', new=zenoh_mock):
            zenoh_client = ZenohClient()

            with pytest.raises(ClientRequestTimeout):
                await zenoh_client.write_property(td, prop_name, Faker().pystr(), timeout=timeout)

    await run_test_coroutine(test_coroutine)


@pytest.mark.asyncio
async def test_stop_timeout(zenoh_servient):
    """Attempting to stop an unresponsive connection does not result in an indefinite wait."""

    exposed_thing = next(zenoh_servient.exposed_things)
    prop_name = next(iter(exposed_thing.properties.keys()))
    td = ThingDescription.from_thing(exposed_thing.thing)

    timeout = random.random()

    assert (timeout * 3) < DEFAULT_TIMEOUT_SECS

    zenoh_mock = _build_zenoh_mock()

    async def test_coroutine():
        with patch('wotpy.protocols.zenoh.client.zenoh.open', new=zenoh_mock):
            zenoh_client = ZenohClient(stop_loop_timeout_secs=timeout)

            with pytest.raises(ClientRequestTimeout):
                await zenoh_client.read_property(td, prop_name, timeout=timeout)

    await run_test_coroutine(test_coroutine)
