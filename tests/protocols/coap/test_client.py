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
    client_test_on_property_change_error_async,
    client_test_read_property_async,
    client_test_write_property_async,
)
from wotpy.protocols.coap.client import CoAPClient


@pytest.mark.asyncio
async def test_read_property(coap_servient):
    """Property values may be retrieved using the CoAP binding client."""

    async for servient in coap_servient:
        await client_test_read_property_async(servient, CoAPClient)


@pytest.mark.asyncio
async def test_write_property(coap_servient):
    """Properties may be updated using the CoAP binding client."""

    async for servient in coap_servient:
        await client_test_write_property_async(servient, CoAPClient)


@pytest.mark.asyncio
async def test_on_property_change(coap_servient):
    """The CoAP client can subscribe to property updates."""

    async for servient in coap_servient:
        await client_test_on_property_change_async(servient, CoAPClient)


@pytest.mark.asyncio
async def test_invoke_action(coap_servient):
    """The CoAP client can invoke actions."""

    async for servient in coap_servient:
        await client_test_invoke_action_async(servient, CoAPClient)


@pytest.mark.asyncio
async def test_on_event(coap_servient):
    """The CoAP client can subscribe to event emissions."""

    async for servient in coap_servient:
        await client_test_on_event_async(servient, CoAPClient)


@pytest.mark.asyncio
async def test_invoke_action_error(coap_servient):
    """Errors raised by Actions are propagated propertly by the CoAP binding client."""

    async for servient in coap_servient:
        await client_test_invoke_action_error_async(servient, CoAPClient)


@pytest.mark.asyncio
async def test_on_property_change_error(coap_servient):
    """Errors that arise in the middle of an ongoing Property
    observation are propagated to the subscription as expected."""

    async for servient in coap_servient:
        await client_test_on_property_change_error_async(servient, CoAPClient)
