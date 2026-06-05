#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 CTIC Centro Tecnologico
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

        return value.decode("utf8") if isinstance(value, bytes) else value

    def to_bytes(self, value):
        """Takes an unicode string and encodes it to an UTF8 bytes string."""

        return value.encode("utf8")
