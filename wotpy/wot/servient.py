#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

from six import string_types

from wotpy.wot.wot import WoT


class Servient(object):
    """An entity that is both a WoT client and server at the same time.
    WoT servers are Web servers that possess capabilities to access underlying
    IoT devices and expose a public interface named the WoT Interface that may
    be used by other clients.
    WoT clients are entities that are able to understand the WoT Interface to
    send requests and interact with IoT devices exposed by other WoT servients
    or servers using the capabilities of a Web client such as Web browser. """

    def __init__(self, hostname=None):
        self._hostname = hostname or socket.getfqdn()
        assert isinstance(self._hostname, string_types), "Invalid hostname"
        self._servers = {}
        self._exposed_things = {}

    def _clean_protocol_links(self, exposed_thing, protocol):
        """Removes all interaction links related to this
        server protocol for the given ExposedThing."""

        assert exposed_thing in self._exposed_things.values()
        assert protocol in self._servers

        for interaction in exposed_thing.thing.interaction:
            links_to_remove = [
                link for link in interaction.link
                if link.protocol == protocol
            ]

            for link in links_to_remove:
                interaction.remove_link(link)

    def _server_has_exposed_thing(self, server, exposed_thing):
        """Returns True if the given server contains the ExposedThing."""

        assert server in self._servers.values()
        assert exposed_thing in self._exposed_things.values()

        try:
            server.get_exposed_thing(exposed_thing.name)
            return True
        except ValueError:
            return False

    def _add_interaction_links(self, server, exposed_thing):
        """Builds and adds to the ExposedThing the Links related to the given server."""

        assert server in self._servers.values()
        assert exposed_thing in self._exposed_things.values()

        for interaction in exposed_thing.thing.interaction:
            links = server.links_for_interaction(
                hostname=self._hostname,
                exposed_thing=exposed_thing,
                interaction=interaction)

            for link in links:
                interaction.add_link(link)

    def _regenerate_server_links(self, server):
        """Cleans and regenerates Links for the given server in all ExposedThings."""

        assert server in self._servers.values()

        for exposed_thing in self._exposed_things.values():
            self._clean_protocol_links(exposed_thing, server.protocol)
            if self._server_has_exposed_thing(server, exposed_thing):
                self._add_interaction_links(server, exposed_thing)

    def add_server(self, server):
        """Adds a new server under this servient."""

        self._servers[server.protocol] = server

    def remove_server(self, protocol):
        """Removes the server with the given protocol from this servient."""

        if protocol not in self._servers:
            raise ValueError("Unknown protocol: {}".format(protocol))

        self._servers.pop(protocol)

    def enable_exposed_thing(self, name):
        """Enables the ExposedThing with the given name.
        This is, the servers will listen for requests for this thing."""

        if name not in self._exposed_things:
            raise ValueError("Unknown thing: {}".format(name))

        for server in self._servers.values():
            exposed_thing = self._exposed_things[name]
            server.add_exposed_thing(exposed_thing)
            self._regenerate_server_links(server)

    def disable_exposed_thing(self, name):
        """Disables the ExposedThing with the given name.
        This is, the servers will not listen for requests for this thing."""

        if name not in self._exposed_things:
            raise ValueError("Unknown thing: {}".format(name))

        for server in self._servers.values():
            server.remove_exposed_thing(name)
            self._regenerate_server_links(server)

    def add_exposed_thing(self, exposed_thing):
        """Adds a ExposedThing to this servient.
        ExposedThings are disabled by default."""

        self._exposed_things[exposed_thing.name] = exposed_thing

    def get_exposed_thing(self, name):
        """Gets a ExposedThing by name."""

        if name not in self._exposed_things:
            raise ValueError("Unknown thing: {}".format(name))

        return self._exposed_things[name]

    def start(self):
        """Starts the servers and returns an instance of the WoT object."""

        for server in self._servers.values():
            server.start()

        return WoT(servient=self)

    def shutdown(self):
        """Stops the server configured under this servient."""

        for server in self._servers.values():
            server.stop()
