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
        self.servers = []
        self.client_factories = {}
        self.things = {}
        self.resource_listeners = {}

    def add_media_type(self, codec):
        """Adds a media type to the list of supported types."""

        pass

    def get_supported_media_types(self):
        """Returns the list of supported media types."""

        pass

    def choose_link(self, interactions):
        """Takes a list of interactions and chooses the most appropriate link."""

        pass

    def add_resource_listener(self, path, resource_listener):
        """Adds a new new resource listener under the given path."""

        pass

    def remove_resource_listener(self, path):
        """Removes the resource listener for the given path."""

        pass

    def add_server(self):
        """Adds a new server under this servient."""

        pass

    def get_servers(self):
        """Returns the current list of servers."""

        pass

    def add_client_factory(self, client_factory):
        """Add a client factory to build clients for
        the requests made by this servient."""

        pass

    def has_client_for(self, scheme):
        """Returns true if a client for the given scheme exists."""

        pass

    def get_client_for(self, scheme):
        """Returns a client for the given scheme."""

        pass

    def get_client_schemes(self):
        """Returns the supported client schemes."""

        pass

    def add_thing_from_td(self, thing_description):
        """Takes a thing description object and builds a
        ExposedThing that is then added to this servient."""

        pass

    def add_thing(self, exposed_thing):
        """Adds a ExposedThing to this servient."""

        pass

    def get_thing(self, name):
        """Gets a ExposedThing by name."""

        pass

    def start(self):
        """Initializes client factories and starts the server.
        Returns an instance of the WoT object."""

        pass

    def shutdown(self):
        """Destroys client factories and stops the servers."""

        pass
