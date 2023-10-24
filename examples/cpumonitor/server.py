"""
WoT application to expose a Thing that provides current host CPU usage levels.
"""

import asyncio
import json
import logging
import os

import coloredlogs
import psutil

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.mqtt.server import MQTTServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient

PORT_CATALOGUE = int(os.environ.get("PORT_CATALOGUE", 9090))
PORT_WS = int(os.environ.get("PORT_WS", 9191))
PORT_HTTP = int(os.environ.get("PORT_HTTP", 9292))
MQTT_BROKER = os.environ.get("MQTT_BROKER", "mqtt://localhost")
DEFAULT_CPU_THRESHOLD = float(os.environ.get("CPU_THRESHOLD", 50.0))
DEFAULT_CPU_CHECK_SEC = float(os.environ.get("CPU_CHECK_SEC", 2.0))
DEFAULT_CPU_UPDATE_SEC = float(os.environ.get("CPU_UPDATE_SEC", 1.0))
HOSTNAME = os.environ.get("HOSTNAME", "localhost")

DESCRIPTION = {
    "id": "urn:org:fundacionctic:thing:cpumonitor",
    "name": "CPU Monitor Thing",
    "properties": {
        "cpuPercent": {
            "description": "Current CPU usage",
            "type": "number",
            "observable": True,
        },
        "cpuThreshold": {
            "description": "CPU usage alert threshold",
            "type": "number",
            "observable": True,
        },
    },
    "events": {
        "cpuAlert": {
            "description": "Alert raised when CPU usage goes over the threshold",
            "data": {"type": "number"},
        }
    },
}

_logger = logging.getLogger("cpumonitor")


async def cpu_percent_loop(exposed_thing):
    _logger.info("Starting loop to update CPU usage")

    while True:
        cpu_value = psutil.cpu_percent()
        await exposed_thing.properties["cpuPercent"].write(cpu_value)
        await asyncio.sleep(DEFAULT_CPU_UPDATE_SEC)


async def cpu_check_loop(exposed_thing):
    """Launches the task that periodically checks for excessive CPU usage."""

    _logger.info("Starting loop to check for excessive CPU usage")

    while True:
        cpu_threshold = await exposed_thing.properties["cpuThreshold"].read()
        cpu_percent = await exposed_thing.properties["cpuPercent"].read()

        if cpu_percent is not None:
            _logger.info("Current CPU usage: {}%".format(cpu_percent))

        if (
            cpu_percent is not None
            and cpu_threshold is not None
            and cpu_percent >= cpu_threshold
        ):
            _logger.info("Emitting CPU alert event")
            exposed_thing.events["cpuAlert"].emit(cpu_percent)

        await asyncio.sleep(DEFAULT_CPU_CHECK_SEC)


async def main():
    """Main entrypoint."""

    _logger.info("Creating WebSocket server on: {}".format(PORT_WS))
    ws_server = WebsocketServer(port=PORT_WS)

    _logger.info("Creating HTTP server on: {}".format(PORT_HTTP))
    http_server = HTTPServer(port=PORT_HTTP)

    _logger.info("Creating MQTT server on broker: {}".format(MQTT_BROKER))
    mqtt_server = MQTTServer(MQTT_BROKER)

    _logger.info("Creating servient with TD catalogue on: {}".format(PORT_CATALOGUE))
    servient = Servient(catalogue_port=PORT_CATALOGUE, hostname=HOSTNAME)
    servient.add_server(ws_server)
    servient.add_server(http_server)
    servient.add_server(mqtt_server)

    _logger.info("Starting servient")
    wot = await servient.start()

    _logger.info("Exposing System Monitor Thing")
    exposed_thing = wot.produce(json.dumps(DESCRIPTION))
    await exposed_thing.properties["cpuThreshold"].write(DEFAULT_CPU_THRESHOLD)
    exposed_thing.expose()

    task_cpu_check = asyncio.create_task(cpu_check_loop(exposed_thing))
    task_cpu_update = asyncio.create_task(cpu_percent_loop(exposed_thing))
    await asyncio.gather(task_cpu_check, task_cpu_update)


if __name__ == "__main__":
    coloredlogs.install(level="DEBUG")
    asyncio.run(main())
