#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six
from tornado.escape import to_unicode


class FutureTimeout(object):
    """Enumeration of default timeouts used to retrieve Future results."""

    MINIMAL = 2
    SHORT = 15
    MEDIUM = 40
    LONG = 120


def assert_equal_dict(dict_a, dict_b, compare_as_unicode=False):
    """Asserts that both dicts are equal."""

    assert set(dict_a.keys()) == set(dict_b.keys())

    for key in dict_a:
        value_a = dict_a[key]
        value_b = dict_b[key]

        if compare_as_unicode and isinstance(value_a, six.string_types):
            assert to_unicode(value_a) == to_unicode(value_b)
        else:
            assert value_a == value_b
