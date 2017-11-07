#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.wot.wot import WoT


class Servient(object):
    """An entity that is both a WoT client and server at the same time.
    WoT servers are Web servers that possess capabilities to access underlying
    IoT devices and expose a public interface named the WoT Interface that may
    be used by other clients.
    WoT clients are entities that are able to understand the WoT Interface to
    send requests and interact with IoT devices exposed by other WoT servients
    or servers using the capabilities of a Web client such as Web browser. """

    def __init__(self):
        self._servers = []
        self._exposed_things = {}

    def add_server(self, server):
        """Adds a new server under this servient."""

        try:
            next(item for item in self._servers if item.protocol == server.protocol)
            raise ValueError("Existing protocol")
        except StopIteration:
            self._servers.append(server)

    def remove_server(self, protocol):
        """Removes the server with the given protocol from this servient."""

        try:
            pop_idx = next(idx for idx, item in enumerate(self._servers) if item.protocol == protocol)
            self._servers.pop(pop_idx)
        except StopIteration:
            pass

    def add_exposed_thing(self, exposed_thing):
        """Adds a ExposedThing to this servient."""

        self._exposed_things[exposed_thing.name] = exposed_thing

    def get_exposed_thing(self, name):
        """Gets a ExposedThing by name."""

        if name not in self._exposed_things:
            raise ValueError("Thing not found: {}".format(name))

        return self._exposed_things[name]

    def start(self):
        """Starts the servers and returns an instance of the WoT object."""

        for server in self._servers:
            server.start()

        return WoT(servient=self)

    def shutdown(self):
        """Stops the server configured under this servient."""

        for server in self._servers:
            server.stop()
