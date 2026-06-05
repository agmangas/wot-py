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

import json

from tests.utils import assert_equal_dict
from wotpy.codecs.json_codec import JsonCodec


def test_json_codec():
    """Content may be serialized to and deserialized from JSON."""

    test_dict = {'unicode': 'áéíóú', 'ascii': 'hello', 'num': 100}
    test_unicode = u'{"unicode": "áéíóú", "ascii": "hello", "num": 100}'
    test_bytes = test_unicode.encode('utf8')

    json_codec = JsonCodec()

    dict_from_unicode = json_codec.to_value(test_unicode)
    dict_from_bytes = json_codec.to_value(test_bytes)
    bytes_from_dict = json_codec.to_bytes(test_dict)

    assert_equal_dict(dict_from_unicode, test_dict, compare_as_unicode=True)
    assert_equal_dict(dict_from_bytes, test_dict, compare_as_unicode=True)

    assert isinstance(bytes_from_dict, bytes)
    assert_equal_dict(json.loads(bytes_from_dict), test_dict, compare_as_unicode=True)
