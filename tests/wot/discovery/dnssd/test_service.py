#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

import pytest
import tornado.gen
import tornado.ioloop
from aiozeroconf import ServiceStateChange, ServiceInfo
from faker import Faker
from six.moves import range

from tests.utils import find_free_port, run_test_coroutine
from wotpy.wot.discovery.dnssd.service import DNSSDDiscoveryService, build_servient_service_info
from wotpy.wot.servient import Servient


def _assert_service_added_removed(servient, service_history, instance_name=None):
    """Checks the service change history to assert that
    the servient service has been added and then removed."""

    info = build_servient_service_info(servient, instance_name=instance_name)
    servient_items = [item for item in service_history if item[1] == info.name]

    assert servient_items[-1][0] == service_history[-2][0] == DNSSDDiscoveryService.WOT_SERVICE_TYPE
    assert servient_items[-2][2] == ServiceStateChange.Added
    assert servient_items[-1][2] == ServiceStateChange.Removed


def _num_service_instance_items(servient, service_history, instance_name=None):
    """Returns the number of items in the given service history that match the servient."""

    info = build_servient_service_info(servient, instance_name=instance_name)
    return len([item for item in service_history if item[1] == info.name])


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

    run_test_coroutine(test_coroutine)


def test_register(asyncio_zeroconf, dnssd_discovery):
    """WoT Servients may be registered for discovery on the DNS-SD service."""

    @tornado.gen.coroutine
    def test_coroutine():
        service_history = asyncio_zeroconf.pop("service_history")

        port_catalogue = find_free_port()
        servient = Servient(catalogue_port=port_catalogue)

        with pytest.raises(ValueError):
            yield dnssd_discovery.register(servient)

        yield dnssd_discovery.start()

        assert not len(service_history)

        yield dnssd_discovery.register(servient)

        while _num_service_instance_items(servient, service_history) < 1:
            yield tornado.gen.sleep(0.1)

        yield dnssd_discovery.stop()

        while _num_service_instance_items(servient, service_history) < 2:
            yield tornado.gen.sleep(0.1)

        _assert_service_added_removed(servient, service_history)

    run_test_coroutine(test_coroutine)


def test_unregister(asyncio_zeroconf, dnssd_discovery):
    """WoT Servients that have been previously registered
    on the DNS-SD service can be unregistered."""

    @tornado.gen.coroutine
    def test_coroutine():
        service_history = asyncio_zeroconf.pop("service_history")

        port_catalogue = find_free_port()
        servient = Servient(catalogue_port=port_catalogue)

        yield dnssd_discovery.start()
        yield dnssd_discovery.register(servient)
        yield dnssd_discovery.unregister(servient)

        while _num_service_instance_items(servient, service_history) < 2:
            yield tornado.gen.sleep(0.1)

        _assert_service_added_removed(servient, service_history)

    run_test_coroutine(test_coroutine)


def test_find(asyncio_zeroconf, dnssd_discovery):
    """Remote WoT Servients may be discovered using the DNS-SD service."""

    @tornado.gen.coroutine
    def test_coroutine():
        aio_zc = asyncio_zeroconf.pop("zeroconf")

        ipaddr = Faker().ipv4_private()
        port = find_free_port()
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

        with pytest.raises(ValueError):
            yield dnssd_discovery.find()

        yield dnssd_discovery.start()

        assert (ipaddr, port) in (yield dnssd_discovery.find(timeout=3))

    run_test_coroutine(test_coroutine)


def test_register_instance_name(asyncio_zeroconf, dnssd_discovery):
    """WoT Servients may be registered with custom service instance names."""

    @tornado.gen.coroutine
    def test_coroutine():
        service_history = asyncio_zeroconf.pop("service_history")

        port_catalogue = find_free_port()
        servient = Servient(catalogue_port=port_catalogue)

        instance_name = Faker().sentence()
        instance_name = instance_name.strip('.')[:32]

        yield dnssd_discovery.start()
        yield dnssd_discovery.register(servient, instance_name=instance_name)

        while _num_service_instance_items(servient, service_history, instance_name) < 1:
            yield tornado.gen.sleep(0.1)

        yield dnssd_discovery.stop()

        while _num_service_instance_items(servient, service_history, instance_name) < 2:
            yield tornado.gen.sleep(0.1)

        assert len([item[1].startswith(instance_name) for item in service_history]) == 2

        with pytest.raises(Exception):
            _assert_service_added_removed(servient, service_history)

        _assert_service_added_removed(servient, service_history, instance_name)

    run_test_coroutine(test_coroutine)


def test_enable_on_servient(asyncio_zeroconf, dnssd_servient):
    """The DNS-SD service may be enabled directly on the
    Servient to avoid the need of explicit instantiation."""

    @tornado.gen.coroutine
    def test_coroutine():
        service_history = asyncio_zeroconf.pop("service_history")
        instance_name = dnssd_servient.dnssd_instance_name

        yield dnssd_servient.start()

        while _num_service_instance_items(dnssd_servient, service_history, instance_name) < 1:
            yield tornado.gen.sleep(0.1)

        yield dnssd_servient.shutdown()

        while _num_service_instance_items(dnssd_servient, service_history, instance_name) < 2:
            yield tornado.gen.sleep(0.1)

        _assert_service_added_removed(dnssd_servient, service_history, instance_name)

    run_test_coroutine(test_coroutine)
