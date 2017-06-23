#!/usr/bin/env python
# -*- coding: utf-8 -*-


class Servient(object):
    """"""

    def __init__(self):
        """"""

        self.servers = []
        self.client_factories = {}
        self.things = {}
        self.resource_listeners = {}

    def add_media_type(self, codec):
        """"""

        pass

    def get_supported_media_types(self):
        """"""

        pass

    def choose_link(self, interactions):
        """"""

        pass

    def add_resource_listener(self, path, resource_listener):
        """"""

        pass

    def remove_resource_listener(self, path):
        """"""

        pass

    def add_server(self):
        """"""

        pass

    def get_servers(self):
        """"""

        pass

    def add_client_factory(self, client_factory):
        """"""

        pass

    def has_client_for(self, scheme):
        """"""

        pass

    def get_client_for(self, scheme):
        """"""

        pass

    def get_client_schemes(self):
        """"""

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
