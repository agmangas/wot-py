#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Functions to check for support for discovery mechanisms.
"""

import platform
import sys

DNSSD_MIN_VERSION = (3, 4, 0)
DNSSD_PLATFORMS = ["Linux", "Darwin"]


def is_dnssd_supported():
    """Returns True if DNS-SD is supported in this platform."""

    return sys.version_info >= DNSSD_MIN_VERSION and platform.system() in DNSSD_PLATFORMS
