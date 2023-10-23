#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
