#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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
WoT application that exposes a Thing with interactions
to check the performance of the Servient.
"""

import argparse
import asyncio
import json
import logging
import pprint
import random
import time
import uuid

from wotpy.wot.enums import DataType

try:
    from . import utils
except ImportError:
    import utils

DESCRIPTION = {
    "id": "urn:org:fundacionctic:thing:benchmark",
    "title": "Benchmark Thing",
    "@context": [
        "https://www.w3.org/2019/wot/td/v1",
    ],
    "securityDefinitions": {
        "nosec_sc":{
            "scheme":"nosec"
        }
    },
    "security": "nosec_sc",
    "properties": {
        "currentTime": {
            "type": DataType.INTEGER,
            "readOnly": True
        }
    },
    "actions": {
        "measureRoundTrip": {
            "safe": True,
            "idempotent": False,
            "input": {
                "type": DataType.OBJECT
            },
            "output": {
                "type": DataType.OBJECT
            }
        },
        "startEventBurst": {
            "safe": True,
            "idempotent": False,
            "input": {
                "type": DataType.OBJECT
            }
        }
    },
    "events": {
        "burstEvent": {
            "data": {
                "type": DataType.OBJECT
            }
        }
    }
}

utils.init_logging()
logger = logging.getLogger()

DEFAULT_RTRIP_MU = 0.0
DEFAULT_RTRIP_SIGMA = 1.0
DEFAULT_RTRIP_LOOP_SLEEP = 0.1
DEFAULT_BURST_LAMBD = 5.0
DEFAULT_BURST_TOTAL = 10


def time_millis():
    """Returns the current timestamp as an integer with ms precision."""

    return int(time.time() * 1000)


async def current_time_handler():
    """Custom handler for the currentTime property."""

    return time_millis()


async def measure_round_trip(parameters):
    """Handler for the action used to measure round trip time."""

    time_arrival = time_millis()

    input_dict = parameters["input"] if parameters["input"] else {}

    mu = input_dict.get("mu", DEFAULT_RTRIP_MU)
    sigma = input_dict.get("sigma", DEFAULT_RTRIP_SIGMA)
    sleep_secs = abs(random.gauss(mu, sigma))
    sleep_end = time.time() + sleep_secs

    while time.time() < sleep_end:
        await asyncio.sleep(DEFAULT_RTRIP_LOOP_SLEEP)

    time_return = time_millis()

    input_dict.update({
        "timeArrival": time_arrival,
        "timeReturn": time_return
    })

    return input_dict


def build_event_burst_handler(exposed_thing):
    """Factory function to build the handler for the action that initiates event bursts."""

    async def start_event_burst(parameters):
        """Emits a series of events where the total count and interval
        between each emission is determined by the given parameters."""

        time_start = time_millis()

        input_dict = parameters["input"] if parameters["input"] else {}

        lambd = input_dict.get("lambd", DEFAULT_BURST_LAMBD)
        total = input_dict.get("total", DEFAULT_BURST_TOTAL)
        burst_id = input_dict.get("id", uuid.uuid4().hex)

        for idx in range(total):
            exposed_thing.emit_event("burstEvent", {
                "id": burst_id,
                "index": idx,
                "timeStart": time_start,
                "timeEmission": time_millis(),
                "burstEnd": idx == total - 1
            })

            await asyncio.sleep(random.expovariate(lambd))

    return start_event_burst


async def main(parsed_args):
    """Main entrypoint."""

    servient = utils.build_servient(parsed_args)

    wot = await servient.start()

    logger.info("Exposing:\n{}".format(pprint.pformat(DESCRIPTION)))

    exposed_thing = wot.produce(json.dumps(DESCRIPTION))
    exposed_thing.set_action_handler("measureRoundTrip", measure_round_trip)
    exposed_thing.set_action_handler("startEventBurst", build_event_burst_handler(exposed_thing))
    exposed_thing.set_property_read_handler("currentTime", current_time_handler)
    exposed_thing.expose()


def parse_args():
    """Parses and returns the command line arguments."""

    parser = argparse.ArgumentParser(description="Benchmark Thing WoT server")
    parser = utils.extend_server_arg_parser(parser)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    loop = asyncio.new_event_loop()
    loop.create_task(main(args))
    loop.run_forever()

