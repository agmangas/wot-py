#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
        self._things = {}
        self._resource_listeners = {}

    @property
    def servers(self):
        """Servient servers property."""

        return self._servers

    @property
    def exposed_things(self):
        """Servient exposed things property."""

        return self._things

    def add_server(self):
        """Adds a new server under this servient."""

        pass

    def add_exposed_thing(self, exposed_thing):
        """Adds a ExposedThing to this servient."""

        pass

    def get_exposed_thing(self, name):
        """Gets a ExposedThing by name."""

        pass

    def add_resource_listener(self, path, resource_listener):
        """Adds a new new resource listener under the given path."""

        pass

    def remove_resource_listener(self, path):
        """Removes the resource listener for the given path."""

        pass

    def start(self):
        """Initializes client factories and starts the server.
        Returns an instance of the WoT object."""

        pass

    def shutdown(self):
        """Destroys client factories and stops the servers."""

        pass
