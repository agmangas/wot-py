#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 National Technical University of Athens
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

import asyncio
import logging
import os

import zenoh

from wotpy.protocols.zenoh.utils import build_zenoh_config

ENV_ROUTER_URL = "WOTPY_TESTS_ZENOH_ROUTER_URL"
ROUTER_SKIP_REASON = "The test Zenoh router is offline"


def get_test_router_url():
    """Returns the Zenoh router URL defined in the environment."""

    return os.environ.get(ENV_ROUTER_URL, None)


async def is_test_router_online():
    """Returns True if the Zenoh router defined in the environment is online."""

    async def check_conn():
        session = None

        router_url = get_test_router_url()

        if not router_url:
            logging.warning("Undefined Zenoh router URL")
            return False

        try:
            config = build_zenoh_config(router_url)
            session = zenoh.open(config)
        except Exception as ex:
            logging.warning("Zenoh router connection error: {}".format(ex))
            return False

        if session is not None:
            session.close()
        return True

    conn_ok = await check_conn()

    if conn_ok is False:
        logging.warning(
            "Couldn't connect to the test Zenoh router. "
            "Please check the {} variable".format(ENV_ROUTER_URL))

    return conn_ok
