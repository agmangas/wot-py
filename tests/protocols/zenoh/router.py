#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
