#!/usr/bin/env python

import asyncio
import json
import logging
import os

import psutil

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.mqtt.server import MQTTServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

logging.basicConfig()
LOGGER = logging.getLogger("sysmonitor")
LOGGER.setLevel(logging.INFO)

PORT_CATALOGUE = int(os.environ.get("PORT_CATALOGUE", 9292))
PORT_WS = int(os.environ.get("PORT_WS", 9191))
PORT_HTTP = int(os.environ.get("PORT_HTTP", 9090))
MQTT_BROKER = os.environ.get("MQTT_BROKER", "mqtt://localhost")
DEFAULT_CPU_THRESHOLD = float(os.environ.get("CPU_THRESHOLD", 50.0))
DEFAULT_CPU_CHECK_SEC = float(os.environ.get("CPU_CHECK_SEC", 2.0))

DESCRIPTION = {
    "id": "urn:org:fundacionctic:thing:cpumonitor",
    "name": "CPU Monitor Thing",
    "properties": {
        "cpuPercent": {
            "description": "Current CPU usage",
            "type": "number",
            "readOnly": True,
            "observable": True
        },
        "cpuThreshold": {
            "description": "CPU usage alert threshold",
            "type": "number",
            "observable": True
        }
    },
    "events": {
        "cpuAlert": {
            "description": "Alert raised when CPU usage goes over the threshold",
            "data": {
                "type": "number"
            }
        }
    }
}


async def cpu_percent_handler():
    """Read handler for the cpuPercent property."""

    return psutil.cpu_percent(interval=1)


def create_cpu_check_task(exposed_thing):
    """Launches the task that periodically checks for excessive CPU usage."""

    async def check_cpu_loop():
        """Coroutine that periodically checks for CPU usage."""

        while True:
            cpu_threshold = await exposed_thing.properties["cpuThreshold"].read()
            cpu_percent = await exposed_thing.properties["cpuPercent"].read()

            LOGGER.info("Current CPU usage: {}%".format(cpu_percent))

            if cpu_percent >= cpu_threshold:
                LOGGER.info("Emitting CPU alert event")
                exposed_thing.events["cpuAlert"].emit(cpu_percent)

            await asyncio.sleep(DEFAULT_CPU_CHECK_SEC)

    event_loop = asyncio.get_event_loop()
    event_loop.create_task(check_cpu_loop())


async def main():
    """Main entrypoint."""

    LOGGER.info("Creating WebSocket server on: {}".format(PORT_WS))

    ws_server = WebsocketServer(port=PORT_WS)

    LOGGER.info("Creating HTTP server on: {}".format(PORT_HTTP))

    http_server = HTTPServer(port=PORT_HTTP)

    LOGGER.info("Creating MQTT server on broker: {}".format(MQTT_BROKER))

    mqtt_server = MQTTServer(MQTT_BROKER)

    LOGGER.info("Creating servient with TD catalogue on: {}".format(PORT_CATALOGUE))

    servient = Servient()
    servient.add_server(ws_server)
    servient.add_server(http_server)
    servient.add_server(mqtt_server)
    servient.enable_td_catalogue(PORT_CATALOGUE)

    LOGGER.info("Starting servient")

    wot = await servient.start()

    LOGGER.info("Exposing System Monitor Thing")

    exposed_thing = wot.produce(json.dumps(DESCRIPTION))
    exposed_thing.set_property_read_handler("cpuPercent", cpu_percent_handler)
    exposed_thing.properties["cpuThreshold"].write(DEFAULT_CPU_THRESHOLD)
    exposed_thing.expose()

    create_cpu_check_task(exposed_thing)


if __name__ == "__main__":
    LOGGER.info("Starting loop")

    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
