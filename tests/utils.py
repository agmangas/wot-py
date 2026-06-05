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

import os
import socket

import tornado.ioloop
from tornado.escape import to_unicode

DEFAULT_TIMEOUT_SECS = 30
TIMEOUT_CORO_VAR = "WOTPY_TESTS_CORO_TIMEOUT"


def run_test_coroutine(coro, timeout=None):
    """Synchronously runs the given test coroutine with an optinally defined timeout."""

    timeout = (
        timeout if timeout else os.getenv(TIMEOUT_CORO_VAR, str(DEFAULT_TIMEOUT_SECS))
    )

    tornado.ioloop.IOLoop.current().run_sync(coro, timeout=float(timeout))


def assert_equal_dict(dict_a, dict_b, compare_as_unicode=False):
    """Asserts that both dicts are equal."""

    assert set(dict_a.keys()) == set(dict_b.keys())

    for key in dict_a:
        value_a = dict_a[key]
        value_b = dict_b[key]

        if compare_as_unicode and isinstance(value_a, str):
            assert to_unicode(value_a) == to_unicode(value_b)
        else:
            assert value_a == value_b


def find_free_port():
    """Returns a free TCP port by attempting to open a socket on an OS-assigned port."""

    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", 0))
        return sock.getsockname()[1]
    finally:
        if sock:
            sock.close()


def is_github_actions() -> bool:
    """Returns True if the current environment is GitHub Actions."""

    return bool(os.getenv("GITHUB_ACTION")) and bool(os.getenv("CI"))
