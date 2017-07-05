#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.codecs.base import BaseCodec


class TextCodec(BaseCodec):
    """Text codec class."""

    MEDIA_TYPE_TEXT = 'text/plain'

    @property
    def media_types(self):
        """Returns the text media types."""

        return [self.MEDIA_TYPE_TEXT]

    def to_value(self, value):
        """Takes an encoded value from a request that may be a UTF8 bytes
        or unicode string and decodes it to an unicode string."""

        return value.decode('utf8') if isinstance(value, bytes) else value

    def to_bytes(self, value):
        """Takes an unicode string and encodes it to an UTF8 bytes string."""

        return value.encode('utf8')
