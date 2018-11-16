#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
