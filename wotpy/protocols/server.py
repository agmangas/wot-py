#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseProtocolServer(object):
    """Base protocol server class."""

    def add_resource(self, path, resource_listener):
        """Adds a resource listener under the given path."""

        raise NotImplementedError()

    def remove_resource(self, path):
        """Removes the resource listener under the given path."""

        raise NotImplementedError()

    def start(self):
        """Starts the server."""

        raise NotImplementedError()

    def stop(self):
        """Stops the server."""

        raise NotImplementedError()

    @property
    def port(self):
        """Port getter."""

        return None

    @property
    def scheme(self):
        """Scheme getter."""

        return None
