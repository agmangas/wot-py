#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents a WoT servient.
"""

import socket

import six
import tornado.web

from wotpy.protocols.enums import Protocols
from wotpy.protocols.ws.client import WebsocketClient
from wotpy.td.description import ThingDescription
from wotpy.wot.exposed import ExposedThingGroup
from wotpy.wot.wot import WoT


class Servient(object):
    """An entity that is both a WoT client and server at the same time.
    WoT servers are Web servers that possess capabilities to access underlying
    IoT devices and expose a public interface named the WoT Interface that may
    be used by other clients.
    WoT clients are entities that are able to understand the WoT Interface to
    send requests and interact with IoT devices exposed by other WoT servients
    or servers using the capabilities of a Web client such as Web browser."""

    def __init__(self, hostname=None):
        self._hostname = hostname or socket.getfqdn()
        assert isinstance(self._hostname, six.string_types), "Invalid hostname"
        self._servers = {}
        self._clients = {}
        self._catalogue_port = None
        self._catalogue_server = None
        self._exposed_thing_group = ExposedThingGroup()

        self._build_default_clients()

    @property
    def exposed_thing_group(self):
        """Returns the ExposedThingGroup instance that
        contains the ExposedThings of this servient."""

        return self._exposed_thing_group

    @property
    def clients(self):
        """Returns the dict of Protocol Binding clients attached to this servient."""

        return self._clients

    def _build_default_clients(self):
        """Builds the default Protocol Binding clients."""

        self._clients.update({
            Protocols.WEBSOCKETS: WebsocketClient()
        })

    def _get_base_url(self, exposed_thing):
        """Return the base URL for the given ExposedThing
        for one of the currently active servers."""

        assert self._exposed_thing_group.contains(exposed_thing)

        if not len(self._servers):
            return None

        protocol = sorted(list(self._servers.keys()))[0]
        server = self._servers[protocol]

        return server.build_base_url(hostname=self._hostname, thing=exposed_thing.thing)

    def _build_td_catalogue_app(self):
        """Returns a Tornado app that provides one endpoint to retrieve the
        entire catalogue of thing descriptions contained in this servient."""

        servient = self

        # noinspection PyAbstractClass
        class TDCatalogueHandler(tornado.web.RequestHandler):
            """Handler that returns a JSON list containing
            all thing descriptions from this servient."""

            def get(self):
                descriptions = {}

                for exp_thing in servient._exposed_thing_group.exposed_things:
                    base_url = servient._get_base_url(exp_thing)
                    td_key = exp_thing.thing.id
                    td_doc = ThingDescription.from_thing(exp_thing.thing).to_dict()
                    td_doc.update({"base": base_url})
                    descriptions[td_key] = td_doc

                self.write(descriptions)

        return tornado.web.Application([(r"/", TDCatalogueHandler)])

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

    def _clean_protocol_forms(self, exposed_thing, protocol):
        """Removes all interaction forms linked to this
        server protocol for the given ExposedThing."""

        assert self._exposed_thing_group.contains(exposed_thing)
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
        assert self._exposed_thing_group.contains(exposed_thing)

        return server.exposed_thing_group.contains(exposed_thing)

    def _add_interaction_forms(self, server, exposed_thing):
        """Builds and adds to the ExposedThing the Links related to the given server."""

        assert server in self._servers.values()
        assert self._exposed_thing_group.contains(exposed_thing)

        for interaction in exposed_thing.thing.interactions:
            forms = server.build_forms(hostname=self._hostname, interaction=interaction)

            for form in forms:
                interaction.add_form(form)

    def _regenerate_server_forms(self, server):
        """Cleans and regenerates Links for the given server in all ExposedThings."""

        assert server in self._servers.values()

        for exp_thing in self._exposed_thing_group.exposed_things:
            self._clean_protocol_forms(exp_thing, server.protocol)
            if self._server_has_exposed_thing(server, exp_thing):
                self._add_interaction_forms(server, exp_thing)

    def add_client(self, client):
        """Adds a new Protocol Binding client to this servient."""

        self._clients[client.protocol] = client

    def remove_client(self, protocol):
        """Removes the Protocol Binding client with the given protocol from this servient."""

        self._clients.pop(protocol, None)

    def add_server(self, server):
        """Adds a new Protocol Binding server to this servient."""

        self._servers[server.protocol] = server

    def remove_server(self, protocol):
        """Removes the Protocol Binding server with the given protocol from this servient."""

        self._servers.pop(protocol, None)

    def enable_exposed_thing(self, name):
        """Enables the ExposedThing with the given name.
        This is, the servers will listen for requests for this thing."""

        exposed_thing = self.get_exposed_thing(name)

        for server in self._servers.values():
            server.add_exposed_thing(exposed_thing)
            self._regenerate_server_forms(server)

    def disable_exposed_thing(self, name):
        """Disables the ExposedThing with the given name.
        This is, the servers will not listen for requests for this thing."""

        exposed_thing = self.get_exposed_thing(name)

        for server in self._servers.values():
            server.remove_exposed_thing(exposed_thing.name)
            self._regenerate_server_forms(server)

    def add_exposed_thing(self, exposed_thing):
        """Adds a ExposedThing to this servient.
        ExposedThings are disabled by default."""

        self._exposed_thing_group.add(exposed_thing)

    def get_exposed_thing(self, name):
        """Finds and returns an ExposedThing contained in this servient by name.
        Raises ValueError if the ExposedThing is not present."""

        exp_thing = self._exposed_thing_group.find(name)

        if exp_thing is None:
            raise ValueError("Unknown Exposed Thing: {}".format(name))

        return exp_thing

    def enable_td_catalogue(self, port):
        """Enables the servient TD catalogue in the given port."""

        self._catalogue_port = port

    def disable_td_catalogue(self):
        """Disables the servient TD catalogue."""

        self._catalogue_port = None

    def start(self):
        """Starts the servers and returns an instance of the WoT object."""

        for server in self._servers.values():
            server.start()

        self._start_catalogue()

        return WoT(servient=self)

    def shutdown(self):
        """Stops the server configured under this servient."""

        for server in self._servers.values():
            server.stop()

        self._stop_catalogue()
