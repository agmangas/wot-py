#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions to check if some functionalities are enabled in the current platform.
"""

import logging
import platform
import sys

FEATURE_DNSSD = "DNSSD"
FEATURE_COAP = "COAP"
FEATURE_MQTT = "MQTT"

FEATURE_REQUISITES = {
    FEATURE_DNSSD: {
        "max_version_exclusive": (3, 13),
        "min_version_inclusive": (3, 7),
        "platforms": ["Linux", "Darwin"],
    },
    FEATURE_COAP: {
        "max_version_exclusive": (3, 13),
        "min_version_inclusive": (3, 7),
        "platforms": ["Linux"],
    },
    FEATURE_MQTT: {
        "max_version_exclusive": (3, 13),
        "min_version_inclusive": (3, 8),
        "platforms": ["Linux", "Darwin"],
    },
}

_logger = logging.getLogger(__name__)


def _is_version_gte(version_a, version_b):
    """Returns True if version_a is greater or equal than version_b."""

    if version_a[0] > version_b[0]:
        return True

    if version_a[0] < version_b[0]:
        return False

    if version_a[1] > version_b[1]:
        return True

    if version_a[1] < version_b[1]:
        return False

    return True


def is_supported(feature):
    """Returns True if the given feature is supported in this platform."""

    reqs = FEATURE_REQUISITES.get(feature)

    if not reqs:
        raise ValueError("Unknown feature: {}".format(feature))

    vinfo = sys.version_info

    min_version = reqs.get("min_version_inclusive")

    if min_version and not _is_version_gte((vinfo.major, vinfo.minor), min_version):
        return False

    max_version = reqs.get("max_version_exclusive")

    if max_version and _is_version_gte((vinfo.major, vinfo.minor), max_version):
        return False

    platforms = reqs.get("platforms")

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
