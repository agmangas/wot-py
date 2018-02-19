#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the text codec.
"""

from wotpy.codecs.base import BaseCodec
from wotpy.codecs.enums import MediaTypes


class TextCodec(BaseCodec):
    """Text codec class."""

    @property
    def media_types(self):
        """Returns the text media types."""

        return [MediaTypes.TEXT]

    def to_value(self, value):
        """Takes an encoded value from a request that may be a UTF8 bytes
        or unicode string and decodes it to an unicode string."""

        return value.decode('utf8') if isinstance(value, bytes) else value

    def to_bytes(self, value):
        """Takes an unicode string and encodes it to an UTF8 bytes string."""

        return value.encode('utf8')
