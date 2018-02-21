#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the abstract server interface.
"""

from abc import ABCMeta, abstractmethod

from wotpy.protocols.enums import ProtocolSchemes
from wotpy.wot.exposed import ExposedThingGroup


class BaseProtocolServer(object):
    """Base protocol server class.
    This is the interface that must be implemented by all server classes."""

    __metaclass__ = ABCMeta

    def __init__(self, port, protocol):
        self._port = port
        self._protocol = protocol
        self._codecs = []
        self._exposed_thing_group = ExposedThingGroup()

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
    def exposed_thing_group(self):
        """Returns the ExposedThingGroup instance that
        contains the ExposedThings of this server."""

        return self._exposed_thing_group

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
        """Adds the given ExposedThing to this server."""

        self._exposed_thing_group.add(exposed_thing)

    def remove_exposed_thing(self, name):
        """Removes the given ExposedThing from this server."""

        self._exposed_thing_group.remove(name)

    def get_exposed_thing(self, name):
        """Finds and returns an ExposedThing contained in this server by name.
        Raises ValueError if the ExposedThing is not present."""

        exposed_thing = self._exposed_thing_group.find(name)

        if exposed_thing is None:
            raise ValueError("Unknown Exposed Thing: {}".format(name))

        return exposed_thing

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
