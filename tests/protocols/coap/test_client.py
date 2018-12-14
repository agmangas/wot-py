#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tests.protocols.helpers import \
    client_test_on_property_change, \
    client_test_on_event, \
    client_test_read_property, \
    client_test_write_property, \
    client_test_invoke_action, \
    client_test_invoke_action_error, \
    client_test_on_property_change_error
from wotpy.protocols.coap.client import CoAPClient


def test_read_property(coap_servient):
    """The CoAP client can read properties."""

    client_test_read_property(coap_servient, CoAPClient)


def test_write_property(coap_servient):
    """The CoAP client can write properties."""

    client_test_write_property(coap_servient, CoAPClient)


def test_on_property_change(coap_servient):
    """The CoAP client can subscribe to property updates."""

    client_test_on_property_change(coap_servient, CoAPClient)


def test_on_property_change_error(coap_servient):
    """Errors that arise in the middle of an ongoing Property
    observation are propagated to the subscription as expected."""

    client_test_on_property_change_error(coap_servient, CoAPClient)


def test_invoke_action(coap_servient):
    """The CoAP client can invoke actions."""

    client_test_invoke_action(coap_servient, CoAPClient)


def test_invoke_action_error(coap_servient):
    """Errors raised by Actions are propagated propertly by the CoAP binding client."""

    client_test_invoke_action_error(coap_servient, CoAPClient)


def test_on_event(coap_servient):
    """The CoAP client can subscribe to event emissions."""

    client_test_on_event(coap_servient, CoAPClient)
