#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
DNS Service Discovery (based on Multicast DNS) Thing discovery service.

.. autosummary::
    :toctree: _dnssd

    wotpy.wot.discovery.dnssd.service
"""

from wotpy.support import is_dnssd_supported

if is_dnssd_supported() is False:
    raise NotImplementedError("DNS-SD is not supported in this platform")
