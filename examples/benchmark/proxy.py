#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2019 CTIC Centro Tecnologico
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
WoT application that consumes a Thing and exposes
another that serves as a proxy for the first.
"""

import argparse
import asyncio
import json
import logging
import pprint

from wotpy.wot.td import ThingDescription

try:
    from . import utils
except ImportError:
    import utils

utils.init_logging()
logger = logging.getLogger()

THING_ID = 'urn:org:fundacionctic:thing:proxy'
SUB_DELAY = 2.0

TIMEOUT_PROP_READ = 120.0
TIMEOUT_PROP_WRITE = 120.0
TIMEOUT_ACTION_INVOCATION = 1800.0
TIMEOUT_HARD_FACTOR = 1.2


def build_prop_read_proxy(consumed_thing, name):
    """Factory for proxy Property read handlers."""

    async def _proxy():
        timeout_soft = TIMEOUT_PROP_READ
        timeout_hard = TIMEOUT_PROP_READ * TIMEOUT_HARD_FACTOR

        awaitable = consumed_thing.properties[name].read(timeout=timeout_soft)

        return await asyncio.wait_for(awaitable, timeout=timeout_hard)

    return _proxy


def build_prop_write_proxy(consumed_thing, name):
    """Factory for proxy Property write handlers."""

    async def _proxy(val):
        timeout_soft = TIMEOUT_PROP_WRITE
        timeout_hard = TIMEOUT_PROP_WRITE * TIMEOUT_HARD_FACTOR

        awaitable = consumed_thing.properties[name].write(val, timeout=timeout_soft)

        await asyncio.wait_for(awaitable, timeout=timeout_hard)

    return _proxy


def build_action_invoke_proxy(consumed_thing, name):
    """Factory for proxy Action invocation handlers."""

    async def _proxy(params):
        timeout_soft = TIMEOUT_ACTION_INVOCATION
        timeout_hard = TIMEOUT_ACTION_INVOCATION * TIMEOUT_HARD_FACTOR

        awaitable = consumed_thing.actions[name].invoke(params.get('input'), timeout=timeout_soft)

        return await asyncio.wait_for(awaitable, timeout=timeout_hard)

    return _proxy


def subscribe_event(consumed_thing, exposed_thing, name):
    """Creates and maintains a subscription to the given Event, recreating it on error."""

    state = {'sub': None}

    def _on_next(item):
        logger.info("{}".format(item))
        exposed_thing.events[name].emit(item.data)

    def _on_completed():
        logger.info("Completed (Event {})".format(name))

    def _on_error(err):
        logger.warning("Error (Event {}) :: {}".format(name, err))

        try:
            logger.warning("Disposing of erroneous subscription")
            state['sub'].dispose()
        except Exception as ex:
            logger.warning("Error disposing: {}".format(ex), exc_info=True)

        def _sub():
            logger.warning("Recreating subscription")
            state['sub'] = consumed_thing.events[name].subscribe(
                on_next=_on_next,
                on_completed=_on_completed,
                on_error=_on_error)

        logger.warning("Re-creating subscription in {} seconds".format(SUB_DELAY))

        asyncio.get_event_loop().call_later(SUB_DELAY, _sub)

    state['sub'] = consumed_thing.events[name].subscribe(
        on_next=_on_next,
        on_completed=_on_completed,
        on_error=_on_error)


async def expose_proxy(wot, consumed_thing):
    """Takes a Consumed Thing and exposes an Exposed Thing that acts as a proxy."""

    description = {
        "id": THING_ID,
        "name": "Thing Proxy: {}".format(consumed_thing.name)
    }

    td_dict = consumed_thing.td.to_dict()

    for intrct_key in ['properties', 'actions', 'events']:
        description.update({intrct_key: td_dict.get(intrct_key, {})})

    exposed_thing = wot.produce(json.dumps(description))

    for name in description.get('properties').keys():
        exposed_thing.set_property_read_handler(name, build_prop_read_proxy(consumed_thing, name))
        exposed_thing.set_property_write_handler(name, build_prop_write_proxy(consumed_thing, name))

    for name in description.get('actions').keys():
        exposed_thing.set_action_handler(name, build_action_invoke_proxy(consumed_thing, name))

    for name in description.get('events').keys():
        subscribe_event(consumed_thing, exposed_thing, name)

    exposed_thing.expose()

    logger.info("Exposed Thing proxy TD:\n{}".format(
        pprint.pformat(ThingDescription.from_thing(exposed_thing.thing).to_dict())))

    return exposed_thing


async def main(parsed_args):
    """Main entrypoint."""

    servient = utils.build_servient(parsed_args)
    wot = await servient.start()
    consumed_thing = await wot.consume_from_url(parsed_args.td_url)
    logger.info("Building Exposed Thing proxy for Consumed Thing: {}".format(consumed_thing))
    await expose_proxy(wot, consumed_thing)


def parse_args():
    """Parses and returns the command line arguments."""

    parser = argparse.ArgumentParser(description="WoT Proxy")
    parser = utils.extend_server_arg_parser(parser)

    parser.add_argument(
        "--url",
        dest="td_url",
        required=True,
        help="Proxied Thing TD URL")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    loop = asyncio.get_event_loop()
    loop.create_task(main(args))
    loop.run_forever()
