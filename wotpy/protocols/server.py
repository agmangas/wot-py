#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod


class BaseProtocolServer(object):
    """Base protocol server class."""

    __metaclass__ = ABCMeta

    def __init__(self, port, scheme):
        self._port = port
        self._scheme = scheme
        self._codecs = []
        self._exposed_things = {}

    @property
    def port(self):
        """Port property."""

        return self._port

    @property
    def scheme(self):
        """Scheme property."""

        return self._scheme

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

        self._exposed_things[exposed_thing.thing.name] = exposed_thing

    def remove_exposed_thing(self, exposed_thing):
        """Removes the given exposed thing from this server."""

        try:
            self._exposed_things.pop(exposed_thing.thing.name)
        except KeyError:
            pass

    @abstractmethod
    def regenerate_links(self):
        """Regenerates all link sub-documents for each interaction
        in the exposed things contained in this server."""

        raise NotImplementedError()

    @abstractmethod
    def start(self):
        """Starts the server."""

        raise NotImplementedError()

    @abstractmethod
    def stop(self):
        """Stops the server."""

        raise NotImplementedError()
