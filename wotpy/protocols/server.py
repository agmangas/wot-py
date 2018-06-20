#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the abstract server interface.
"""

from abc import ABCMeta, abstractmethod

from wotpy.wot.exposed.group import ExposedThingGroup


class BaseProtocolServer(object):
    """Base protocol server class.
    This is the interface that must be implemented by all server classes."""

    __metaclass__ = ABCMeta

    def __init__(self, port):
        self._port = port
        self._codecs = []
        self._exposed_thing_group = ExposedThingGroup()

    @property
    @abstractmethod
    def protocol(self):
        """Server protocol."""

        raise NotImplementedError()

    @property
    def port(self):
        """Port property."""

        return self._port

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

    def remove_exposed_thing(self, thing_id):
        """Removes the given ExposedThing from this server."""

        self._exposed_thing_group.remove(thing_id)

    def get_exposed_thing(self, name):
        """Finds and returns an ExposedThing contained in this server by name.
        Raises ValueError if the ExposedThing is not present."""

        exposed_thing = self._exposed_thing_group.find_by_thing_id(name)

        if exposed_thing is None:
            raise ValueError("Unknown Exposed Thing: {}".format(name))

        return exposed_thing

    @abstractmethod
    def build_forms(self, hostname, interaction):
        """Builds and returns a list with all Form that are
        linked to this server for the given Interaction."""

        raise NotImplementedError()

    @abstractmethod
    def build_base_url(self, hostname, thing):
        """Returns the base URL for the given Thing in the context of this server."""

        raise NotImplementedError()

    @abstractmethod
    def start(self):
        """Starts the server."""

        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        """Stops the server."""

        raise NotImplementedError()
