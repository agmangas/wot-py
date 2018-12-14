#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

import six
from tornado.escape import to_unicode


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


def find_free_port():
    """Returns a free TCP port by attempting to open a socket on an OS-assigned port."""

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", 0))
        return sock.getsockname()[1]
    finally:
        # noinspection PyUnboundLocalVariable
        sock.close()
