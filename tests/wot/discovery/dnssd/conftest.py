#!/usr/bin/env python
# -*- coding: utf-8 -*-

import collections
import logging
import socket

import pytest
import tornado.gen
import tornado.ioloop
from faker import Faker

from tests.utils import find_free_port
from wotpy.support import is_dnssd_supported
from wotpy.wot.servient import Servient

collect_ignore = []

if not is_dnssd_supported():
    logging.warning("Skipping DNS-SD tests due to unsupported platform")
    collect_ignore.extend(["test_service.py"])


@pytest.fixture
def asyncio_zeroconf():
    """Builds an aiozeroconf service instance and starts browsing for WoT Servient services.
    Provides a deque that contains the service state change history."""

    from aiozeroconf import Zeroconf, ServiceBrowser
    from wotpy.wot.discovery.dnssd.service import DNSSDDiscoveryService

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

    loop.run_sync(close)


@pytest.fixture
def dnssd_discovery():
    """Builds an instance of the DNS-SD service."""

    from wotpy.wot.discovery.dnssd.service import DNSSDDiscoveryService

    dnssd_discovery = DNSSDDiscoveryService()

    yield dnssd_discovery

    @tornado.gen.coroutine
    def stop():
        yield dnssd_discovery.stop()

    tornado.ioloop.IOLoop.current().run_sync(stop)


@pytest.fixture
def dnssd_servient():
    """Builds a Servient with both the TD catalogue and the DNS-SD service enabled."""

    servient = Servient(
        catalogue_port=find_free_port(),
        dnssd_enabled=True,
        dnssd_instance_name=Faker().pystr())

    yield servient

    @tornado.gen.coroutine
    def shutdown():
        yield servient.shutdown()

    tornado.ioloop.IOLoop.current().run_sync(shutdown)
