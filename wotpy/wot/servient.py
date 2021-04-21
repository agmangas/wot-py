#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents a WoT servient.
"""

import functools
import re
import socket

import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.locks
import tornado.web
from wotpy.protocols.enums import Protocols
from wotpy.protocols.http.client import HTTPClient
from wotpy.protocols.ws.client import WebsocketClient
from wotpy.support import (is_coap_supported, is_dnssd_supported,
                           is_mqtt_supported)
from wotpy.utils.utils import get_main_ipv4_address
from wotpy.wot.enums import InteractionTypes
from wotpy.wot.exposed.thing_set import ExposedThingSet
from wotpy.wot.td import ThingDescription
from wotpy.wot.wot import WoT


class TDHandler(tornado.web.RequestHandler):
    """Handler that returns the TD document of a given Thing."""

    def initialize(self, servient):
        self.servient = servient

    def get(self, thing_url_name):
        exp_thing = self.servient.exposed_thing_set.find_by_thing_id(
            thing_url_name)

        td_doc = ThingDescription.from_thing(exp_thing.thing).to_dict()
        base_url = self.servient.get_thing_base_url(exp_thing)

        if base_url:
            td_doc.update({"base": base_url})

        self.write(td_doc)


class TDCatalogueHandler(tornado.web.RequestHandler):
    """Handler that returns the entire catalogue of Things contained in this servient.
    May return TDs in expanded format or URL pointers to the individual TDs."""

    def initialize(self, servient):
        self.servient = servient

    def get(self):
        response = {}

        for exp_thing in self.servient.enabled_exposed_things:
            thing_id = exp_thing.thing.id

            if self.get_argument("expanded", False):
                val = ThingDescription.from_thing(exp_thing.thing).to_dict()
                val.update(
                    {"base": self.servient.get_thing_base_url(exp_thing)})
            else:
                val = "/{}".format(exp_thing.thing.url_name)

            response[thing_id] = val

        self.write(response)


class ServientStateException(Exception):
    """Exception raised when the user modifies the Servient while
    the Servient is in an inappropriate state."""

    pass


def _stopped_servient_only(func):
    """Decorator that raises an Exception when attempting
    to call the function while the Servient is running."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        servient = args[0]

        if servient.is_running:
            raise ServientStateException(
                "Attempted to modify the Servient while it was running")

        return func(*args, **kwargs)

    return wrapper


_REGEX_HOSTNAME = r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z]{2,}$"
_REGEX_ARPA = r".*\.(ip6|in-addr)\.arpa$"


def _get_hostname_fallback():
    """Tries to guess the hostname of the current host that should be used on TD Forms.
    Two strategies are used for this: First, the socket.getfqdn() method. If the returned
    value is not a FQDN then we try to get the IPv4 address of the main network interface."""

    fqdn = socket.getfqdn()

    valid_fqdn = re.search(_REGEX_HOSTNAME, fqdn) \
        and not re.search(_REGEX_ARPA, fqdn)

    return fqdn if valid_fqdn else get_main_ipv4_address()


class Servient(object):
    """An entity that is both a WoT client and server at the same time.
    WoT servers are Web servers that possess capabilities to access underlying
    IoT devices and expose a public interface named the WoT Interface that may
    be used by other clients.
    WoT clients are entities that are able to understand the WoT Interface to
    send requests and interact with IoT devices exposed by other WoT servients
    or servers using the capabilities of a Web client such as Web browser."""

    def __init__(self, hostname=None, catalogue_port=9090,
                 clients=None, clients_config=None,
                 dnssd_enabled=False, dnssd_instance_name=None):
        self._hostname = hostname if hostname is not None else _get_hostname_fallback()

        if not isinstance(self._hostname, six.string_types):
            raise ValueError("Invalid hostname: {}".format(self._hostname))

        if isinstance(clients, list):
            clients = {item.protocol: item for item in clients}

        self._servers = {}
        self._clients = clients if clients else {}
        self._clients_config = clients_config
        self._catalogue_port = catalogue_port
        self._catalogue_server = None
        self._exposed_thing_set = ExposedThingSet()
        self._servient_lock = tornado.locks.Lock()
        self._is_running = False
        self._dnssd_enabled = dnssd_enabled if dnssd_enabled and is_dnssd_supported() else False
        self._dnssd_instance_name = dnssd_instance_name
        self._dnssd = None
        self._enabled_exposed_thing_ids = set()

        if not len(self._clients):
            self._build_default_clients()

    @staticmethod
    def _default_select_client(clients, td, name):
        """Default implementation of the function to select
        a Protocol Binding client for an Interaction."""

        protocol_preference_map = {
            InteractionTypes.PROPERTY: [
                Protocols.HTTP,
                Protocols.COAP,
                Protocols.WEBSOCKETS,
                Protocols.MQTT
            ],
            InteractionTypes.ACTION: [
                Protocols.WEBSOCKETS,
                Protocols.MQTT,
                Protocols.COAP,
                Protocols.HTTP
            ],
            InteractionTypes.EVENT: [
                Protocols.WEBSOCKETS,
                Protocols.MQTT,
                Protocols.COAP,
                Protocols.HTTP
            ]
        }

        supported_protocols = [
            client.protocol for client in clients
            if client.is_supported_interaction(td, name)
        ]

        intrct_names = {
            InteractionTypes.PROPERTY: six.iterkeys(td.properties),
            InteractionTypes.ACTION: six.iterkeys(td.actions),
            InteractionTypes.EVENT: six.iterkeys(td.events)
        }

        try:
            intrct_type = next(key for key, names in six.iteritems(
                intrct_names) if name in names)
        except StopIteration:
            raise ValueError("Unknown interaction: {}".format(name))

        protocol_prefs = protocol_preference_map[intrct_type]
        protocol_choices = set(protocol_prefs).intersection(
            set(supported_protocols))

        if not len(protocol_choices):
            return list(clients)[0]

        protocol = next(
            proto for proto in protocol_prefs if proto in protocol_choices)

        return next(client for client in clients if client.protocol == protocol)

    @property
    def is_running(self):
        """Returns True if the Servient is currently running
        (i.e. the attached servers have been started)."""

        return self._is_running

    @property
    def hostname(self):
        """Hostname attached to this servient."""

        return self._hostname

    @property
    def exposed_thing_set(self):
        """Returns the ExposedThingSet instance that
        contains the ExposedThings of this servient."""

        return self._exposed_thing_set

    @property
    def exposed_things(self):
        """Returns an iterator for the ExposedThings contained in this Servient."""

        return self.exposed_thing_set.exposed_things

    @property
    def enabled_exposed_things(self):
        """Returns an iterator for the enabled ExposedThings contained in this Servient."""

        for exposed_thing in self.exposed_things:
            if exposed_thing.id in self._enabled_exposed_thing_ids:
                yield exposed_thing

    @property
    def servers(self):
        """Returns the dict of Protocol Binding servers attached to this servient."""

        return self._servers

    @property
    def clients(self):
        """Returns the dict of Protocol Binding clients attached to this servient."""

        return self._clients

    @property
    def catalogue_port(self):
        """Returns the current port of the HTTP Thing Description catalogue service."""

        return self._catalogue_port

    @catalogue_port.setter
    @_stopped_servient_only
    def catalogue_port(self, port):
        """Enables the servient TD catalogue in the given port."""

        self._catalogue_port = port

    @property
    def dnssd(self):
        """Returns the DNS-SD instance linked to this Servient (if enabled and started)."""

        return self._dnssd

    @property
    def dnssd_instance_name(self):
        """Returns the user-given DNS-SD service instance name."""

        return self._dnssd_instance_name

    @tornado.gen.coroutine
    def _start_dnssd(self):
        """Starts the DNS-SD service and registers the servient."""

        if self._dnssd or not self._dnssd_enabled:
            return

        from wotpy.wot.discovery.dnssd.service import DNSSDDiscoveryService

        self._dnssd = DNSSDDiscoveryService()

        yield self._dnssd.start()
        yield self._dnssd.register(self, instance_name=self._dnssd_instance_name)

    @tornado.gen.coroutine
    def _stop_dnssd(self):
        """Unregisters the servient and stops the DNS-SD service."""

        if not self._dnssd:
            return

        yield self._dnssd.stop()

        self._dnssd = None

    def _build_default_clients(self):
        """Builds the default Protocol Binding clients."""

        self._clients = self._clients if self._clients else {}

        conf = self._clients_config if self._clients_config else {}

        self._clients.update({
            Protocols.WEBSOCKETS: WebsocketClient(**conf.get(Protocols.WEBSOCKETS, {})),
            Protocols.HTTP: HTTPClient(**conf.get(Protocols.HTTP, {}))
        })

        if is_coap_supported():
            from wotpy.protocols.coap.client import CoAPClient
            self._clients.update(
                {Protocols.COAP: CoAPClient(**conf.get(Protocols.COAP, {}))})

        if is_mqtt_supported():
            from wotpy.protocols.mqtt.client import MQTTClient
            self._clients.update(
                {Protocols.MQTT: MQTTClient(**conf.get(Protocols.MQTT, {}))})

    def _build_td_catalogue_app(self):
        """Returns a Tornado app that provides one endpoint to retrieve the
        entire catalogue of thing descriptions contained in this servient."""

        return tornado.web.Application([
            (r"/", TDCatalogueHandler, dict(servient=self)),
            (r"/(?P<thing_url_name>[^\/]+)", TDHandler, dict(servient=self))
        ])

    def _start_catalogue(self):
        """Starts the TD catalogue server if enabled."""

        if self._catalogue_server or not self._catalogue_port:
            return

        catalogue_app = self._build_td_catalogue_app()
        self._catalogue_server = catalogue_app.listen(self._catalogue_port)

    def _stop_catalogue(self):
        """Stops the TD catalogue server if running."""

        if not self._catalogue_server:
            return

        self._catalogue_server.stop()
        self._catalogue_server = None

    def _clean_forms(self):
        """Cleans all the Forms from all the ExposedThings contained in this Servient."""

        for exposed_thing in self._exposed_thing_set.exposed_things:
            for interaction in exposed_thing.thing.interactions:
                interaction.clean_forms()

    def _clean_protocol_forms(self, exposed_thing, protocol):
        """Removes all interaction forms linked to this
        server protocol for the given ExposedThing."""

        assert self._exposed_thing_set.contains(exposed_thing)
        assert protocol in self._servers

        for interaction in exposed_thing.thing.interactions:
            forms_to_remove = [
                form for form in interaction.forms
                if form.protocol == protocol
            ]

            for form in forms_to_remove:
                interaction.remove_form(form)

    def _server_has_exposed_thing(self, server, exposed_thing):
        """Returns True if the given server contains the ExposedThing."""

        assert server in self._servers.values()
        assert self._exposed_thing_set.contains(exposed_thing)

        return server.exposed_thing_set.contains(exposed_thing)

    def _add_interaction_forms(self, server, exposed_thing):
        """Builds and adds to the ExposedThing the Links related to the given server."""

        assert server in self._servers.values()
        assert self._exposed_thing_set.contains(exposed_thing)

        for interaction in exposed_thing.thing.interactions:
            forms = server.build_forms(
                hostname=self._hostname, interaction=interaction)

            for form in forms:
                interaction.add_form(form)

    def _regenerate_server_forms(self, server):
        """Cleans and regenerates Forms for the given server in all ExposedThings."""

        assert server in self._servers.values()

        for exp_thing in self._exposed_thing_set.exposed_things:
            self._clean_protocol_forms(exp_thing, server.protocol)
            if self._server_has_exposed_thing(server, exp_thing):
                self._add_interaction_forms(server, exp_thing)

    def get_thing_base_url(self, exposed_thing):
        """Return the base URL for the given ExposedThing
        for one of the currently active servers."""

        if exposed_thing.thing.base:
            return exposed_thing.base

        if not self.exposed_thing_set.contains(exposed_thing):
            raise ValueError("Unknown ExposedThing")

        if not len(self.servers):
            return None

        protocol_default = sorted(six.iterkeys(self.servers))[0]
        protocol = Protocols.HTTP if Protocols.HTTP in self.servers else protocol_default
        server = self.servers[protocol]

        return server.build_base_url(hostname=self.hostname, thing=exposed_thing.thing)

    def select_client(self, td, name):
        """Returns the Protocol Binding client instance to
        communicate with the given Interaction."""

        return Servient._default_select_client(self.clients.values(), td, name)

    @_stopped_servient_only
    def add_client(self, client):
        """Adds a new Protocol Binding client to this servient."""

        self._clients[client.protocol] = client

    @_stopped_servient_only
    def remove_client(self, protocol):
        """Removes the Protocol Binding client with the given protocol from this servient."""

        self._clients.pop(protocol, None)

    @_stopped_servient_only
    def add_server(self, server):
        """Adds a new Protocol Binding server to this servient."""

        self._servers[server.protocol] = server

    @_stopped_servient_only
    def remove_server(self, protocol):
        """Removes the Protocol Binding server with the given protocol from this servient."""

        self._servers.pop(protocol, None)

    def refresh_forms(self):
        """Cleans and regenerates Forms for all the
        ExposedThings and servers contained in this servient."""

        self._clean_forms()

        for server in self._servers.values():
            self._regenerate_server_forms(server)

    def enable_exposed_thing(self, thing_id):
        """Enables the ExposedThing with the given ID.
        This is, the servers will listen for requests for this thing."""

        exposed_thing = self.get_exposed_thing(thing_id)

        for server in self._servers.values():
            server.add_exposed_thing(exposed_thing)
            self._regenerate_server_forms(server)

        self._enabled_exposed_thing_ids.add(exposed_thing.id)

    def disable_exposed_thing(self, thing_id):
        """Disables the ExposedThing with the given ID.
        This is, the servers will not listen for requests for this thing."""

        exposed_thing = self.get_exposed_thing(thing_id)

        if exposed_thing.id not in self._enabled_exposed_thing_ids:
            raise ValueError(
                "ExposedThing {} is already disabled".format(thing_id))

        for server in self._servers.values():
            server.remove_exposed_thing(exposed_thing.id)
            self._regenerate_server_forms(server)

        self._enabled_exposed_thing_ids.remove(exposed_thing.id)

    def add_exposed_thing(self, exposed_thing):
        """Adds an ExposedThing to this Servient.
        ExposedThings are disabled by default."""

        self._exposed_thing_set.add(exposed_thing)

    def remove_exposed_thing(self, thing_id):
        """Disables and removes an ExposedThing from this Servient."""

        if thing_id in self._enabled_exposed_thing_ids:
            self.disable_exposed_thing(thing_id)

        self._exposed_thing_set.remove(thing_id)

    def get_exposed_thing(self, thing_id):
        """Finds and returns an ExposedThing contained in this servient by Thing ID.
        Raises ValueError if the ExposedThing is not present."""

        exp_thing = self._exposed_thing_set.find_by_thing_id(thing_id)

        if exp_thing is None:
            raise ValueError("Unknown ExposedThing: {}".format(thing_id))

        return exp_thing

    @_stopped_servient_only
    def disable_td_catalogue(self):
        """Disables the servient TD catalogue."""

        self._catalogue_port = None

    @tornado.gen.coroutine
    def start(self):
        """Starts the servers and returns an instance of the WoT object."""

        with (yield self._servient_lock.acquire()):
            self.refresh_forms()
            yield [server.start() for server in six.itervalues(self._servers)]
            self._start_catalogue()
            yield self._start_dnssd()
            self._is_running = True

            raise tornado.gen.Return(WoT(servient=self))

    @tornado.gen.coroutine
    def shutdown(self):
        """Stops the server configured under this servient."""

        with (yield self._servient_lock.acquire()):
            yield [server.stop() for server in six.itervalues(self._servers)]
            self._stop_catalogue()
            yield self._stop_dnssd()
            self._is_running = False
