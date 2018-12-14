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
from wotpy.protocols.http.client import HTTPClient


def test_read_property(http_servient):
    """The HTTP client can read properties."""

    client_test_read_property(http_servient, HTTPClient)


def test_write_property(http_servient):
    """The HTTP client can write properties."""

    client_test_write_property(http_servient, HTTPClient)


def test_invoke_action(http_servient):
    """The HTTP client can invoke actions."""

    client_test_invoke_action(http_servient, HTTPClient)


def test_invoke_action_error(http_servient):
    """Errors raised by Actions are propagated propertly by the HTTP binding client."""

    client_test_invoke_action_error(http_servient, HTTPClient)


def test_on_event(http_servient):
    """The HTTP client can subscribe to event emissions."""

    client_test_on_event(http_servient, HTTPClient)


def test_on_property_change(http_servient):
    """The HTTP client can subscribe to property updates."""

    client_test_on_property_change(http_servient, HTTPClient)


def test_on_property_change_error(http_servient):
    """Errors that arise in the middle of an ongoing Property
    observation are propagated to the subscription as expected."""

    client_test_on_property_change_error(http_servient, HTTPClient)
