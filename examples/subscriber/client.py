#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
WoT client application that takes a Thing Description URL and
subscribes to all observable properties and events in the consumed Thing.
"""

import argparse
import asyncio
import logging

from wotpy.wot.servient import Servient

logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


async def main(td_url, sleep_time):
    """Subscribes to all events and properties on the remote Thing."""

    wot = await Servient().start()
    consumed_thing = await wot.consume_from_url(td_url)

    LOGGER.info("ConsumedThing: {}".format(consumed_thing))

    subscriptions = []

    def subscribe(intrct):
        LOGGER.info("Subscribing to: {}".format(intrct))

        sub = intrct.subscribe(
            on_next=lambda item: LOGGER.info("{} :: Next :: {}".format(intrct, item)),
            on_completed=lambda: LOGGER.info("{} :: Completed".format(intrct)),
            on_error=lambda error: LOGGER.warning("{} :: Error :: {}".format(intrct, error)))

        subscriptions.append(sub)

    for name in consumed_thing.properties:
        if consumed_thing.properties[name].observable:
            subscribe(consumed_thing.properties[name])

    for name in consumed_thing.events:
        subscribe(consumed_thing.events[name])

    await asyncio.sleep(sleep_time)

    for subscription in subscriptions:
        LOGGER.info("Disposing: {}".format(subscription))
        subscription.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Subscribes to all events and properties")
    parser.add_argument('--url', required=True, help="Thing Description URL")
    parser.add_argument('--time', default=120, type=int, help="Total subscription time (s)")
    args = parser.parse_args()

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(args.url, args.time))
