#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Service discovery based on Multicast DNS and DNS-SD (Bonjour, Avahi).
"""

import socket
import threading
import time
from functools import partial
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


def build_servient_service_info(servient, address=None, instance_name=None):
    """Takes a Servient and optional IP address and builds the
    zeroconf ServiceInfo that describes the WoT Servient service."""

    address = address if address else get_main_ipv4_address()
    servient_urlname = slugify(servient.hostname)
    instance_name = instance_name if instance_name else servient_urlname
    servient_fqdn = "{}.".format(servient.hostname.strip('.'))
    server_default = "{}.local.".format(servient_urlname)
    server = servient_fqdn if servient_fqdn.endswith('.local.') else server_default

    return ServiceInfo(
        DNSSDDiscoveryService.WOT_SERVICE_TYPE,
        "{}.{}".format(instance_name, DNSSDDiscoveryService.WOT_SERVICE_TYPE),
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
    registered_lock = threading.Lock()

    def _on_service_change(*args, **kwargs):
        """Callback for each time a WoT Servient service is added or removed from the link."""

        service_type = kwargs.pop('service_type')
        name = kwargs.pop('name')
        state_change = kwargs.pop('state_change')

        with registered_lock:
            is_local = any(item.name == name for item in registered)

        if is_local:
            return

        def _add_result():
            info = zeroconf.get_service_info(service_type, name)
            info_addr = socket.inet_ntoa(cast(bytes, info.address))
            info_port = cast(int, info.port)

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
        instance_name = task['instance_name']

        try:
            if not servient.catalogue_port:
                return

            info = build_servient_service_info(
                servient,
                address=address,
                instance_name=instance_name)

            with registered_lock:
                registered.append(info)

            zeroconf.register_service(info)
        finally:
            done.set()

    def _unregister(task):
        """Unregisters a WoT Servient service."""

        servient = task['servient']
        done = task['done']
        instance_name = task['instance_name']

        try:
            info = build_servient_service_info(
                servient,
                address=address,
                instance_name=instance_name)

            with registered_lock:
                is_registered = any(val == info for val in registered)

            if not is_registered:
                return

            zeroconf.unregister_service(info)

            with registered_lock:
                registered.remove(info)
        finally:
            done.set()

    def _main_loop():
        """Main Zeroconf service loop that starts browsing for WoT
        services and processes the register tasks queue."""

        browser = None

        try:
            browser = ServiceBrowser(
                zeroconf,
                DNSSDDiscoveryService.WOT_SERVICE_TYPE,
                handlers=[_on_service_change])

            while not close_event.is_set():
                try:
                    register_task = register_queue.get_nowait()

                    task_handler_map = {
                        TASK_REGISTER: _register,
                        TASK_UNREGISTER: _unregister
                    }

                    task_handler_map[register_task['type']](register_task)
                except queue.Empty:
                    pass

                close_event.wait(ITER_WAIT)
        finally:
            if browser is not None:
                browser.cancel()

            with registered_lock:
                for serv_info in registered:
                    zeroconf.unregister_service(serv_info)

            zeroconf.close()

    _main_loop()


class DNSSDDiscoveryService(object):
    """Manages a DNS Service Discovery service (based on Multicast DNS)
    that is run on a separate thread (on a loop executor) to discover
    link-local WoT Servients and expose its own."""

    WOT_SERVICE_TYPE = "_wot-servient._tcp.local."

    def __init__(self, address=None):
        self._address = address
        self._zeroconf_loop_thread = None
        self._close_event = threading.Event()
        self._register_queue = None
        self._lock = tornado.locks.Lock()
        self._loop = tornado.ioloop.IOLoop.current()
        self._services = None
        self._services_lock = threading.Lock()

    @property
    def is_running(self):
        """Returns True if the mDNS service is currently running."""

        return self._zeroconf_loop_thread is not None

    @tornado.gen.coroutine
    def start(self):
        """Starts the DNS-SD thread on a loop executor."""

        with (yield self._lock.acquire()):
            if self._zeroconf_loop_thread is not None:
                return

            self._close_event.clear()
            self._register_queue = queue.Queue()
            self._services = {}

            thread_target = partial(
                _start_zeroconf,
                self._close_event,
                self._services,
                self._services_lock,
                self._register_queue,
                self._address)

            self._zeroconf_loop_thread = threading.Thread(
                target=thread_target,
                daemon=True)

            self._zeroconf_loop_thread.start()

    @tornado.gen.coroutine
    def stop(self):
        """Signals the DNS-SD thread to stop and waits for the executor future to yield."""

        with (yield self._lock.acquire()):
            if self._zeroconf_loop_thread is None:
                return

            self._close_event.set()

            while self._zeroconf_loop_thread.is_alive():
                yield tornado.gen.sleep(ITER_WAIT)

            self._zeroconf_loop_thread = None
            self._close_event.clear()
            self._register_queue = None
            self._services = None

    @tornado.gen.coroutine
    def _run_task(self, task):
        """"""

        with (yield self._lock.acquire()):
            if self._zeroconf_loop_thread is None:
                raise ValueError("Stopped DNS-SD thread")

            done = threading.Event()
            task.update({'done': done})

            self._register_queue.put(task)

            while not done.is_set():
                yield tornado.gen.sleep(ITER_WAIT)

    @tornado.gen.coroutine
    def register(self, servient, instance_name=None):
        """Takes a Servient and registers the TD catalogue
        service for discovery by other hosts in the same link."""

        if instance_name and instance_name.endswith('.'):
            raise ValueError('Instance name ends with "."')

        yield self._run_task({
            'type': TASK_REGISTER,
            'servient': servient,
            'instance_name': instance_name
        })

    @tornado.gen.coroutine
    def unregister(self, servient, instance_name=None):
        """Takes a Servient and unregisters the TD catalogue service."""

        if instance_name and instance_name.endswith('.'):
            raise ValueError('Instance name ends with "."')

        yield self._run_task({
            'type': TASK_UNREGISTER,
            'servient': servient,
            'instance_name': instance_name
        })

    @tornado.gen.coroutine
    def find(self, min_results=None, timeout=5):
        """Browses the link to discover WoT Servient services using mDNS.
        Returns a list of (ip_address, port).
        If min_results is defined it will stop as soon as that number of results are found."""

        with (yield self._lock.acquire()):
            if self._zeroconf_loop_thread is None:
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
