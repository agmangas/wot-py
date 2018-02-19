#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

from wotpy.protocols.enums import ProtocolSchemes


class BaseProtocolServer(object):
    """Base protocol server class."""

    __metaclass__ = ABCMeta

    def __init__(self, port, protocol):
        self._port = port
        self._protocol = protocol
        self._codecs = []
        self._exposed_things = {}

    @property
    def port(self):
        """Port property."""

        return self._port

    @property
    def protocol(self):
        """Protocol property."""

        return self._protocol

    @property
    def scheme(self):
        """Scheme property."""

        return ProtocolSchemes.scheme_for_protocol(self.protocol)

    @property
    def exposed_things(self):
        """Exposed things property."""

        return list(self._exposed_things.values())

    def codec_for_media_type(self, media_type):
        """Returns a BaseCodec to serialize or deserialize content for the given media type."""

        try:
            return next(codec for codec in self._codecs if media_type in codec.media_types)
        except StopIteration:
            raise ValueError('Unknown media type')

    def add_codec(self, codec):
        """Adds a BaseCodec to this server."""

        self._codecs.append(codec)

    def add_exposed_thing(self, exposed_thing):
        """Adds the given exposed thing to this server."""

        if exposed_thing.name in self._exposed_things:
            return

        self._exposed_things[exposed_thing.name] = exposed_thing

    def remove_exposed_thing(self, name):
        """Removes the given exposed thing from this server."""

        if name not in self._exposed_things:
            return

        self._exposed_things.pop(name)

    def get_exposed_thing(self, name):
        """Gets a ExposedThing by name."""

        if name not in self._exposed_things:
            raise ValueError("Not found: {}".format(name))

        return self._exposed_things[name]

    @abstractmethod
    def links_for_interaction(self, hostname, exposed_thing, interaction):
        """Builds and returns a list with all Links that
        relate to this server for the given Interaction."""

        raise NotImplementedError()

    @abstractmethod
    def get_thing_base_url(self, hostname, exposed_thing):
        """Returns the base URL for the given ExposedThing in the context of this server."""

        raise NotImplementedError()

    @abstractmethod
    def start(self):
        """Starts the server."""

        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        """Stops the server."""

        raise NotImplementedError()
