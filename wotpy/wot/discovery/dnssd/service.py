#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Service discovery based on Multicast DNS and DNS-SD (Bonjour, Avahi).
"""

import socket
import threading
import time
from typing import cast

import six
import tornado.gen
import tornado.ioloop
import tornado.locks
from six.moves import queue
from slugify import slugify
from zeroconf import Zeroconf, ServiceStateChange, ServiceInfo, ServiceBrowser

from wotpy.utils.utils import get_main_ipv4_address

ITER_WAIT = 0.1
TASK_REGISTER = 'register'
TASK_UNREGISTER = 'unregister'


def build_servient_service_info(servient, address=None):
    """Takes a Servient and optional IP address and builds the
    zeroconf ServiceInfo that describes the WoT Servient service."""

    address = address if address else get_main_ipv4_address()

    servient_urlname = slugify(servient.hostname)
    servient_fqdn = "{}.".format(servient.hostname.strip('.'))
    server_default = "{}.local.".format(servient_urlname)
    server = servient_fqdn if servient_fqdn.endswith('.local.') else server_default

    return ServiceInfo(
        DNSSDDiscoveryService.WOT_SERVICE_TYPE,
        "{}.{}".format(servient_urlname, DNSSDDiscoveryService.WOT_SERVICE_TYPE),
        port=servient.catalogue_port,
        address=socket.inet_aton(address),
        properties={},
        server=server)


def _start_zeroconf(close_event, services, services_lock, register_queue, address):
    """Starts the zeroconf mDNS service.
    Listens to the register tasks queue and starts browsing for WoT Servient services."""

    address = address if address else get_main_ipv4_address()
    zeroconf = Zeroconf()
    registered = []
    browser = None

    def _on_service_change(*args, **kwargs):
        """Callback for each time a WoT Servient service is added or removed from the link."""

        service_type = kwargs.pop('service_type')
        name = kwargs.pop('name')
        state_change = kwargs.pop('state_change')

        def _add_result():
            info = zeroconf.get_service_info(service_type, name)
            info_addr = socket.inet_ntoa(cast(bytes, info.address))
            info_port = cast(int, info.port)

            if info_addr == address:
                return

            with services_lock:
                services[name] = (info_addr, info_port)

        def _remove_result():
            with services_lock:
                try:
                    services.pop(name)
                except KeyError:
                    pass

        change_handler_map = {
            ServiceStateChange.Added: _add_result,
            ServiceStateChange.Removed: _remove_result
        }

        change_handler_map[state_change]()

    def _register(task):
        """Registers a new WoT Servient service."""

        servient = task['servient']
        done = task['done']

        try:
            if not servient.catalogue_port:
                return

            info = build_servient_service_info(servient, address=address)
            zeroconf.register_service(info)
            registered.append(info)
        finally:
            done.set()

    def _unregister(task):
        """Unregisters a WoT Servient service."""

        servient = task['servient']
        done = task['done']

        try:
            info = build_servient_service_info(servient, address=address)

            if not any(val == info for val in registered):
                return

            zeroconf.unregister_service(info)
            registered.remove(info)
        finally:
            done.set()

    try:
        browser = ServiceBrowser(
            zeroconf,
            DNSSDDiscoveryService.WOT_SERVICE_TYPE,
            handlers=[_on_service_change])

        while not close_event.is_set():
            try:
                item = register_queue.get_nowait()

                task_handler_map = {
                    TASK_REGISTER: _register,
                    TASK_UNREGISTER: _unregister
                }

                task_handler_map[item['type']](item)
            except queue.Empty:
                pass

            close_event.wait(ITER_WAIT)
    finally:
        if browser is not None:
            browser.cancel()

        for item in registered:
            zeroconf.unregister_service(item)

        zeroconf.close()


class DNSSDDiscoveryService(object):
    """Manages a DNS Service Discovery service (based on Multicast DNS)
    that is run on a separate thread (on a loop executor) to discover
    link-local WoT Servients and expose its own."""

    WOT_SERVICE_TYPE = "_wot-servient._tcp.local."

    def __init__(self, address=None):
        self._address = address
        self._zeroconf_loop_future = None
        self._close_event = threading.Event()
        self._register_queue = None
        self._lock = tornado.locks.Lock()
        self._loop = tornado.ioloop.IOLoop.current()
        self._services = None
        self._services_lock = threading.Lock()

    @property
    def is_running(self):
        """Returns True if the mDNS service is currently running."""

        return self._zeroconf_loop_future is not None

    @tornado.gen.coroutine
    def start(self):
        """Starts the DNS-SD thread on a loop executor."""

        with (yield self._lock.acquire()):
            if self._zeroconf_loop_future is not None:
                return

            self._close_event.clear()
            self._register_queue = queue.Queue()
            self._services = {}

            self._zeroconf_loop_future = self._loop.run_in_executor(
                None,
                _start_zeroconf,
                self._close_event,
                self._services,
                self._services_lock,
                self._register_queue,
                self._address)

    @tornado.gen.coroutine
    def stop(self):
        """Signals the DNS-SD thread to stop and waits for the executor future to yield."""

        with (yield self._lock.acquire()):
            if self._zeroconf_loop_future is None:
                return

            self._close_event.set()
            yield self._zeroconf_loop_future
            self._zeroconf_loop_future = None
            self._close_event.clear()
            self._register_queue = None
            self._services = None

    @tornado.gen.coroutine
    def _run_task(self, task):
        """"""

        with (yield self._lock.acquire()):
            if self._zeroconf_loop_future is None:
                raise ValueError("Stopped DNS-SD thread")

            done = threading.Event()
            task.update({'done': done})

            self._register_queue.put(task)

            while not done.is_set():
                yield tornado.gen.sleep(ITER_WAIT)

    @tornado.gen.coroutine
    def register(self, servient):
        """Takes a Servient and registers the TD catalogue
        service for discovery by other hosts in the same link."""

        yield self._run_task({
            'type': TASK_REGISTER,
            'servient': servient
        })

    @tornado.gen.coroutine
    def unregister(self, servient):
        """Takes a Servient and unregisters the TD catalogue service."""

        yield self._run_task({
            'type': TASK_UNREGISTER,
            'servient': servient
        })

    @tornado.gen.coroutine
    def find(self, min_results=None, timeout=5):
        """Browses the link to discover WoT Servient services using mDNS.
        Returns a list of (ip_address, port).
        If min_results is defined it will stop as soon as that number of results are found."""

        with (yield self._lock.acquire()):
            if self._zeroconf_loop_future is None:
                raise ValueError("Stopped DNS-SD thread")

            ini = time.time()
            finished = False

            while (time.time() - ini) < timeout and not finished:
                if min_results is not None:
                    with self._services_lock:
                        if len(self._services) >= min_results:
                            finished = True

                yield tornado.gen.sleep(ITER_WAIT)

            with self._services_lock:
                found = list(six.itervalues(self._services))

            raise tornado.gen.Return(found)
