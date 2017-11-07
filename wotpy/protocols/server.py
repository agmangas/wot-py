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

    def _clean_protocol_links(self):
        """Removes all interaction links for the ExposedThings
        contained in this server that match the server protocol."""

        for exp_thing in self._exposed_things.values():
            for interaction in exp_thing.thing.interaction:
                links_to_remove = [
                    link for link in interaction.link
                    if link.protocol == self.protocol
                ]

                for link in links_to_remove:
                    interaction.remove_link(link)

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
