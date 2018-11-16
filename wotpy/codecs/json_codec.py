#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the JSON codec.
"""

import json

from wotpy.codecs.base import BaseCodec
from wotpy.codecs.enums import MediaTypes


class JsonCodec(BaseCodec):
    """JSON codec class."""

    @property
    def media_types(self):
        """Returns the JSON media types."""

        return [MediaTypes.JSON]

    def to_value(self, value):
        """Takes an encoded value from a request that may be an UTF8 bytes
        or unicode JSON string and deserializes it to a Python object."""

        return json.loads(value)

    def to_bytes(self, value):
        """Takes an object and serializes it to an UTF8 bytes JSON string."""

        json_str = json.dumps(value)

        return json_str if isinstance(json_str, bytes) else json_str.encode('utf8')
