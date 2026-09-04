# Copyright (c) 2018 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
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
WoT application to expose a Thing that provides current host CPU usage levels.
"""

import asyncio
import json
import logging
import os

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
    "title": "CPU Monitor Thing",
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
