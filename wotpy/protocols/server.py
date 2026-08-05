#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Class that represents the abstract server interface.
"""

from abc import ABCMeta, abstractmethod

from wotpy.wot.exposed.thing_set import ExposedThingSet


class BaseProtocolServer(metaclass=ABCMeta):
    """Base protocol server class.
    This is the interface that must be implemented by all server classes."""


    def __init__(self, port, form_port=None):
        self._form_port = port if form_port is None else form_port
        self._port = port
        self._codecs = []
        self._exposed_thing_set = ExposedThingSet()

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
    def form_port(self):
        """Port that will be used inside of forms in case
        it differs from the server's port for example in cases
        of a proxy."""

        return self._form_port

    @property
    def exposed_thing_set(self):
        """Returns the ExposedThingSet instance that
        contains the ExposedThings of this server."""

        return self._exposed_thing_set

    @property
    def exposed_things(self):
        """Returns an iterator for all the ExposedThings contained in this server."""

        return self._exposed_thing_set.exposed_things

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

        self._exposed_thing_set.add(exposed_thing)

    def remove_exposed_thing(self, thing_id):
        """Removes the given ExposedThing from this server."""

        self._exposed_thing_set.remove(thing_id)

    def get_exposed_thing(self, title):
        """Finds and returns an ExposedThing contained in this server by name.
        Raises ValueError if the ExposedThing is not present."""

        exposed_thing = self._exposed_thing_set.find_by_thing_title(title)

        if exposed_thing is None:
            raise ValueError("Unknown Exposed Thing: {}".format(title))

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
    async def start(self, servient):
        """Coroutine that starts the server."""

        raise NotImplementedError()

    @abstractmethod
    async def stop(self):
        """Coroutine that stops the server.
        Some requests could be still in progress and would be served after the server has stopped."""

        raise NotImplementedError()
