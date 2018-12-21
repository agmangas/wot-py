#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

DESCRIPTION = {
    "id": "urn:org:fundacionctic:thing:benchmark",
    "name": "Benchmark Thing",
    "properties": {
        "rwStr": {
            "type": "string",
            "observable": True
        },
        "rwObj": {
            "type": "object",
            "observable": True
        }
    },
    "actions": {
        "measureRoundTrip": {
            "safe": True,
            "idempotent": False,
            "input": {
                "type": "object"
            },
            "output": {
                "type": "object"
            }
        }
    }
}

LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(format=LOG_FORMAT)
logger = logging.getLogger()
logger.setLevel(logging.INFO)


async def measure_round_trip(parameters):
    """Handler for the 'measureRoundTrip' Action."""

    time_arrival = int(time.time() * 1000)

    input_dict = parameters["input"] if parameters["input"] else {}

    mu = input_dict.pop("sleepMu", 0)
    sigma = input_dict.pop("sleepSigma", 1)
    sleep_secs = abs(random.gauss(mu, sigma))

    await asyncio.sleep(sleep_secs)

    time_return = int(time.time() * 1000)

    input_dict.update({
        "timeArrival": time_arrival,
        "timeReturn": time_return
    })

    return input_dict


async def main(parsed_args):
    """Main entrypoint."""

    logger.info("Creating servient with TD catalogue on: {}".format(parsed_args.port_catalogue))

    servient = Servient(
        catalogue_port=parsed_args.port_catalogue,
        hostname=parsed_args.hostname)

    if parsed_args.port_ws > 0:
        logger.info("Creating WebSocket server on: {}".format(parsed_args.port_ws))
        servient.add_server(WebsocketServer(port=parsed_args.port_ws))

    if parsed_args.port_http > 0:
        logger.info("Creating HTTP server on: {}".format(parsed_args.port_http))
        servient.add_server(HTTPServer(port=parsed_args.port_http))

    if parsed_args.mqtt_broker:
        try:
            from wotpy.protocols.mqtt.server import MQTTServer
            logger.info("Creating MQTT server on broker: {}".format(parsed_args.mqtt_broker))
            servient.add_server(MQTTServer(parsed_args.mqtt_broker))
        except NotImplementedError as ex:
            logger.warning(ex)

    if parsed_args.port_coap > 0:
        try:
            from wotpy.protocols.coap.server import CoAPServer
            logger.info("Creating CoAP server on: {}".format(parsed_args.port_coap))
            servient.add_server(CoAPServer(port=parsed_args.port_coap))
        except NotImplementedError as ex:
            logger.warning(ex)

    logger.info("Starting servient")

    wot = await servient.start()

    logger.info("Exposing:\n{}".format(pprint.pformat(DESCRIPTION)))

    exposed_thing = wot.produce(json.dumps(DESCRIPTION))
    exposed_thing.set_action_handler("measureRoundTrip", measure_round_trip)
    exposed_thing.expose()


def parse_args():
    """Parses and returns the command line arguments."""

    parser = argparse.ArgumentParser(description="Benchmark Thing WoT server")

    parser.add_argument(
        '--port-catalogue',
        dest="port_catalogue",
        default=9090,
        type=int,
        help="Thing Description catalogue port")

    parser.add_argument(
        '--port-http',
        dest="port_http",
        default=9191,
        type=int,
        help="HTTP server port")

    parser.add_argument(
        '--port-ws',
        dest="port_ws",
        default=9292,
        type=int,
        help="WebSockets server port")

    parser.add_argument(
        '--port-coap',
        dest="port_coap",
        default=9393,
        type=int,
        help="CoAP server port")

    parser.add_argument(
        '--mqtt-broker',
        dest="mqtt_broker",
        default="mqtt://localhost",
        help="MQTT broker URL")

    parser.add_argument(
        '--hostname',
        dest="hostname",
        default=None,
        help="Servient hostname")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    loop = asyncio.get_event_loop()
    loop.create_task(main(args))
    loop.run_forever()
