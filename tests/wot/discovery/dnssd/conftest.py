#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import logging
import socket

import pytest
import tornado.gen
import tornado.ioloop
from aiozeroconf import Zeroconf, ServiceBrowser

from wotpy.wot.discovery.dnssd.service import DNSSDDiscoveryService
from wotpy.wot.discovery.support import is_dnssd_supported

collect_ignore = []

if not is_dnssd_supported():
    logging.warning("Skipping DNS-SD tests due to unsupported platform")
    collect_ignore.extend(["test_service.py"])


@pytest.fixture
def asyncio_zeroconf():
    """Builds an aiozeroconf service instance and starts browsing for WoT Servient services.
    Provides a deque that contains the service state change history."""

    loop = tornado.ioloop.IOLoop.current()

    service_history = collections.deque([])

    def on_change(zc, service_type, name, state_change):
        service_history.append((service_type, name, state_change))

    aio_zc = Zeroconf(loop.asyncio_loop, address_family=[socket.AF_INET])
    ServiceBrowser(aio_zc, DNSSDDiscoveryService.WOT_SERVICE_TYPE, handlers=[on_change])

    yield {
        "zeroconf": aio_zc,
        "service_history": service_history
    }

    @tornado.gen.coroutine
    def close():
        yield aio_zc.close()

    loop.add_callback(close)
