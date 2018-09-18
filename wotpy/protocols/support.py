#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions to check for support for protocol binding implementations.
"""

import platform
import sys

COAP_MIN_VERSION = (3, 6, 0)
COAP_PLATFORMS = ["Linux"]

MQTT_MIN_VERSION = (3, 6, 0)
MQTT_PLATFORMS = ["Linux", "Darwin"]


def is_coap_supported():
    """Returns True if the CoAP binding is supported in this platform."""

    return sys.version_info >= COAP_MIN_VERSION and platform.system() in COAP_PLATFORMS


def is_mqtt_supported():
    """Returns True if the MQTT binding is supported in this platform."""

    return sys.version_info >= MQTT_MIN_VERSION and platform.system() in MQTT_PLATFORMS
