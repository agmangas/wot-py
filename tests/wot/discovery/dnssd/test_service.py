#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import socket

import pytest
import tornado.gen
import tornado.ioloop
from aiozeroconf import ServiceStateChange, ServiceInfo
from faker import Faker
from six.moves import range

from wotpy.wot.discovery.dnssd.service import DNSSDDiscoveryService, build_servient_service_info
from wotpy.wot.servient import Servient


def test_start_stop():
    """The DNS-SD service can be started and stopped."""

    @tornado.gen.coroutine
    def test_coroutine():
        dnssd_discovery = DNSSDDiscoveryService()

        yield dnssd_discovery.start()

        assert dnssd_discovery.is_running

        for _ in range(10):
            yield dnssd_discovery.stop()

        assert not dnssd_discovery.is_running

        for _ in range(10):
            yield dnssd_discovery.start()

        assert dnssd_discovery.is_running

        yield dnssd_discovery.stop()

        assert not dnssd_discovery.is_running

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def _assert_service_added_removed(servient, service_history):
    """Checks the service change history to assert that
    the servient service has been added and then removed."""

    info = build_servient_service_info(servient)
    servient_items = [item for item in service_history if item[1] == info.name]

    assert servient_items[-1][0] == service_history[-2][0] == DNSSDDiscoveryService.WOT_SERVICE_TYPE
    assert servient_items[-2][2] == ServiceStateChange.Added
    assert servient_items[-1][2] == ServiceStateChange.Removed


@pytest.mark.flaky(reruns=5)
def test_register(asyncio_zeroconf):
    """WoT Servients may be registered for discovery on the DNS-SD service."""

    @tornado.gen.coroutine
    def test_coroutine():
        service_history = asyncio_zeroconf.pop("service_history")

        port_catalogue = random.randint(20000, 40000)
        servient = Servient()
        servient.enable_td_catalogue(port_catalogue)

        dnssd_discovery = DNSSDDiscoveryService()

        with pytest.raises(ValueError):
            yield dnssd_discovery.register(servient)

        yield dnssd_discovery.start()

        assert not len(service_history)

        yield dnssd_discovery.register(servient)

        while not len(service_history):
            yield tornado.gen.sleep(0.1)

        yield dnssd_discovery.stop()

        while len(service_history) < 2:
            yield tornado.gen.sleep(0.1)

        _assert_service_added_removed(servient, service_history)

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_unregister(asyncio_zeroconf):
    """WoT Servients that have been previously registered
    on the DNS-SD service can be unregistered."""

    @tornado.gen.coroutine
    def test_coroutine():
        service_history = asyncio_zeroconf.pop("service_history")

        port_catalogue = random.randint(20000, 40000)
        servient = Servient()
        servient.enable_td_catalogue(port_catalogue)

        dnssd_discovery = DNSSDDiscoveryService()

        yield dnssd_discovery.start()
        yield dnssd_discovery.register(servient)
        yield dnssd_discovery.unregister(servient)

        while len(service_history) < 2:
            yield tornado.gen.sleep(0.1)

        _assert_service_added_removed(servient, service_history)

        yield dnssd_discovery.stop()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_find(asyncio_zeroconf):
    """Remote WoT Servients may be discovered using the DNS-SD service."""

    @tornado.gen.coroutine
    def test_coroutine():
        aio_zc = asyncio_zeroconf.pop("zeroconf")

        ipaddr = Faker().ipv4_private()
        port = random.randint(20000, 40000)
        service_name = "{}.{}".format(Faker().pystr(), DNSSDDiscoveryService.WOT_SERVICE_TYPE)
        server = "{}.local.".format(Faker().pystr())

        info = ServiceInfo(
            DNSSDDiscoveryService.WOT_SERVICE_TYPE,
            service_name,
            address=socket.inet_aton(ipaddr),
            port=port,
            properties={},
            server=server)

        yield aio_zc.register_service(info)

        dnssd_discovery = DNSSDDiscoveryService()

        with pytest.raises(ValueError):
            yield dnssd_discovery.find()

        yield dnssd_discovery.start()

        assert (ipaddr, port) in (yield dnssd_discovery.find(timeout=3))

        yield dnssd_discovery.stop()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
