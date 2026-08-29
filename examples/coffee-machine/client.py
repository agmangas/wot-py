# Copyright (c) 2026 Contributors to the Eclipse Foundation
# Copyright (c) 2023 CTIC Centro Tecnologico
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
This is an example of Web of Things consumer ("client" mode) Thing script.
It considers a fictional smart coffee machine in order to demonstrate the capabilities of Web of Things.
The example is ported from the node-wot environment -
https://github.com/eclipse/thingweb.node-wot/blob/master/packages/examples/src/scripts/coffee-machine-client.ts.
"""

import asyncio
import json
import logging
import urllib.request

from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT

_logger = logging.getLogger("coffee-machine-client")

CATALOGUE_URL = "http://127.0.0.1:9090"
THING_TITLE = "Smart-Coffee-Machine"


async def discover_thing_url(catalogue: str, title: str) -> str:
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None, lambda: urllib.request.urlopen(catalogue).read()
    )
    return json.loads(data)[title]


async def main():
    wot = WoT(servient=Servient())

    consumed_thing = await wot.consume_from_url(
        await discover_thing_url(CATALOGUE_URL, THING_TITLE)
    )

    _logger.info("Consumed Thing: {}".format(consumed_thing))

    # Read property allAvailableResources
    allAvailableResources = await consumed_thing.read_property("allAvailableResources")
    _logger.info("allAvailableResources value is: {}".format(allAvailableResources))

    # Now let's change water level to 80
    allAvailableResources["water"] = 80
    await consumed_thing.write_property("allAvailableResources", allAvailableResources)

    # And see that the water level has changed
    allAvailableResources = await consumed_thing.read_property("allAvailableResources")

    _logger.info(
        "allAvailableResources value after change is: {}".format(allAvailableResources)
    )

    # It's also possible to set a client-side handler for observable properties
    consumed_thing.properties["maintenanceNeeded"].subscribe(
        on_next=lambda data: _logger.info(
            f"Value changed for an observable property: {data}"
        ),
        on_completed=_logger.info(
            "Subscribed for an observable property: maintenanceNeeded"
        ),
        on_error=lambda error: _logger.info(
            f"Error for an observable property maintenanceNeeded: {error}"
        ),
    )

    # Now let's make 3 cups of latte!
    makeCoffee = await consumed_thing.invoke_action(
        "makeDrink", {"drinkId": "latte", "size": "l", "quantity": 3}
    )

    if makeCoffee.get("result"):
        _logger.info("Enjoy your drink! \n{}".format(makeCoffee))
    else:
        _logger.info("Failed making your drink: {}".format(makeCoffee))

    # See how allAvailableResources property value has changed
    allAvailableResources = await consumed_thing.read_property("allAvailableResources")
    _logger.info("allAvailableResources value is: {}".format(allAvailableResources))

    # Let's add a scheduled task
    scheduledTask = await consumed_thing.invoke_action(
        "setSchedule",
        {
            "drinkId": "espresso",
            "size": "m",
            "quantity": 2,
            "time": "10:00",
            "mode": "everyday",
        },
    )

    _logger.info(f'{scheduledTask["message"]} \n{scheduledTask}')

    # See how it has been added to the schedules property
    schedules = await consumed_thing.read_property("schedules")
    _logger.info("schedules value is: \n{}".format(json.dumps(schedules, indent=2)))

    # Let's set up a handler for outOfResource event
    consumed_thing.events["outOfResource"].subscribe(
        on_next=lambda data: _logger.info(f"New event is emitted: {data}"),
        on_completed=_logger.info("Subscribed for an event: outOfResource"),
        on_error=lambda error: _logger.info(
            f"Error for an event outOfResource: {error}"
        ),
    )

    wait_sleep_secs = 60.0
    _logger.info("Waiting for %s seconds...", wait_sleep_secs)
    await asyncio.sleep(wait_sleep_secs)


def _setup_logging() -> None:
    colors = {
        logging.DEBUG: "\033[37m",
        logging.INFO: "\033[36m",
        logging.WARNING: "\033[33m",
        logging.ERROR: "\033[31m",
        logging.CRITICAL: "\033[35m",
    }
    reset = "\033[0m"

    class _ColorFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            record.levelname = f"{colors.get(record.levelno, '')}{record.levelname}{reset}"
            return super().format(record)

    handler = logging.StreamHandler()
    handler.setFormatter(_ColorFormatter("%(asctime)s %(name)s %(levelname)s %(message)s"))
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(handler)


if __name__ == "__main__":
    _setup_logging()
    asyncio.run(main())
