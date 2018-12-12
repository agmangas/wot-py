#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions to check if some functionalities are enabled in the current platform.
"""

import platform
import sys

FEATURE_DNSSD = 'DNSSD'
FEATURE_COAP = 'COAP'
FEATURE_MQTT = 'MQTT'

FEATURE_REQUISITES = {
    FEATURE_DNSSD: {
        'min_version': (3, 4, 0),
        'platforms': ['Linux', 'Darwin']
    },
    FEATURE_COAP: {
        'min_version': (3, 4, 0),
        'platforms': ['Linux']
    },
    FEATURE_MQTT: {
        'min_version': (3, 4, 0),
        'platforms': ['Linux', 'Darwin']
    }
}


def is_supported(feature):
    """Returns True if the given feature is supported in this platform."""

    reqs = FEATURE_REQUISITES.get(feature)

    if not reqs:
        raise ValueError("Unknown feature: {}".format(feature))

    min_version = reqs.get('min_version')

    if min_version and sys.version_info < min_version:
        return False

    platforms = reqs.get('platforms')

    if platforms and platform.system() not in platforms:
        return False

    return True


def is_coap_supported():
    """Returns True if the CoAP binding is supported in this platform."""

    return is_supported(FEATURE_COAP)


def is_mqtt_supported():
    """Returns True if the MQTT binding is supported in this platform."""

    return is_supported(FEATURE_MQTT)


def is_dnssd_supported():
    """Returns True if DNS-SD is supported in this platform."""

    return is_supported(FEATURE_DNSSD)
