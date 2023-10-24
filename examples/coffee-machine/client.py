"""
This is an example of Web of Things consumer ("client" mode) Thing script.
It considers a fictional smart coffee machine in order to demonstrate the capabilities of Web of Things.
The example is ported from the node-wot environment -
https://github.com/eclipse/thingweb.node-wot/blob/master/packages/examples/src/scripts/coffee-machine-client.ts.
"""

import asyncio
import json
import logging

import coloredlogs

from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT

_logger = logging.getLogger("coffee-machine-client")


async def main():
    wot = WoT(servient=Servient())

    consumed_thing = await wot.consume_from_url(
        "http://127.0.0.1:9090/smart-coffee-machine-97e83de1-f5c9-a4a0-23b6-be918d3a22ca"
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


if __name__ == "__main__":
    coloredlogs.install(level="DEBUG")
    asyncio.run(main())
