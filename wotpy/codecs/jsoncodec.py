#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from wotpy.codecs.base import BaseCodec


class JsonCodec(BaseCodec):
    """JSON codec class."""

    MEDIA_TYPE_JSON = 'application/json'

    @property
    def media_types(self):
        """Returns the JSON media types."""

        return [self.MEDIA_TYPE_JSON]

    def to_value(self, value):
        """Takes an encoded value from a request that may be an UTF8 bytes
        or unicode JSON string and deserializes it to a Python object."""

        return json.loads(value)

    def to_bytes(self, value):
        """Takes an object and serializes it to an UTF8 bytes JSON string."""

        json_str = json.dumps(value)

        return json_str if isinstance(json_str, bytes) else json_str.encode('utf8')
