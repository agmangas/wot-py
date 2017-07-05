#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseProtocolServer(object):
    """Base protocol server class."""

    def __init__(self, port, scheme):
        self._port = port
        self._scheme = scheme
        self._codecs = []

    def codec_for_media_type(self, media_type):
        """Returns a BaseCodec to serialize or deserialize content for the given media type."""

        try:
            return next(codec for codec in self._codecs if media_type in codec.media_types)
        except StopIteration:
            raise ValueError('Unknown media type')

    def add_codec(self, codec):
        """Adds a BaseCodec for this server."""

        self._codecs.append(codec)

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

        return self._port

    @property
    def scheme(self):
        """Scheme getter."""

        return self._scheme
