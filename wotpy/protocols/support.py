#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions to check for support for protocol binding implementations.
"""

import platform
import sys

COAP_MIN_VERSION = (3, 5, 2)
COAP_PLATFORMS = ["Linux"]


def is_coap_supported():
    """Returns True if the CoAP binding is supported in this platform."""

    return sys.version_info >= COAP_MIN_VERSION and platform.system() in COAP_PLATFORMS
