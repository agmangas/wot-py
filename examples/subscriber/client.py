"""
WoT client application that takes a Thing Description URL and
subscribes to all observable properties and events in the consumed Thing.
"""

import argparse
import asyncio
import logging

import coloredlogs

from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT

_logger = logging.getLogger("wotsubscriber")


async def main(td_url, sleep_time):
    """Subscribes to all events and properties on the remote Thing."""

    wot = WoT(servient=Servient())
    consumed_thing = await wot.consume_from_url(td_url)

    _logger.info("ConsumedThing: {}".format(consumed_thing))

    subscriptions = []

    def subscribe(intrct):
        _logger.info("Subscribing to: {}".format(intrct))

        sub = intrct.subscribe(
            on_next=lambda item: _logger.info("{} :: Next :: {}".format(intrct, item)),
            on_completed=lambda: _logger.info("{} :: Completed".format(intrct)),
            on_error=lambda error: _logger.warning(
                "{} :: Error :: {}".format(intrct, error)
            ),
        )

        subscriptions.append(sub)

    for name in consumed_thing.properties:
        if consumed_thing.properties[name].observable:
            subscribe(consumed_thing.properties[name])

    for name in consumed_thing.events:
        subscribe(consumed_thing.events[name])

    await asyncio.sleep(sleep_time)

    for subscription in subscriptions:
        _logger.info("Disposing: {}".format(subscription))
        subscription.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Subscribes to all events and properties"
    )
    parser.add_argument("--url", required=True, help="Thing Description URL")
    parser.add_argument(
        "--time", default=120, type=int, help="Total subscription time (s)"
    )
    args = parser.parse_args()

    coloredlogs.install(level="DEBUG")
    asyncio.run(main(args.url, args.time))
