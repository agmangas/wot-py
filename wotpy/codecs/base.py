#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseCodec(object):
    """Base codec class."""

    @property
    def media_types(self):
        """Property getter for the supported media types of this codec."""

        raise NotImplementedError()

    def to_value(self, value):
        """Takes an encoded value from a request that may be an UTF8
        bytes or unicode string and decodes it to a Python object."""

        raise NotImplementedError()

    def to_bytes(self, value):
        """Takes a Python object and encodes it to an UTF8
        bytes string to be included in a response."""

        raise NotImplementedError()
