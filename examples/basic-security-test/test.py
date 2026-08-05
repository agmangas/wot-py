#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import asyncio
import json
import logging

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.coap.server import CoAPServer
from wotpy.wot.servient import Servient

CATALOGUE_PORT = 9090
HTTP_PORT = 9494
COAP_PORT = 5683

logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

TD = {
    "title": "Test",
    "id": "urn:dev:wot:test:test",
    "description": """A test example.""",
    "securityDefinitions": {
        "basic_sc":{
            "scheme":"basic"
        }
    },
    "security": "basic_sc",
    "@context": [
        "https://www.w3.org/2022/wot/td/v1.1",
    ],
    "properties": {
        "dummy": {
            "type": "integer"
        }
    }
}

async def main():
    # LOGGER.info("Creating HTTP server on: {}".format(HTTP_PORT))
    # http_server = HTTPServer(
    #     port=HTTP_PORT,
    #     security_scheme=TD["securityDefinitions"]["basic_sc"])

    LOGGER.info("Creating CoAP server on: {}".format(COAP_PORT))
    coap_server = CoAPServer(
        port=COAP_PORT,
        security_scheme=TD["securityDefinitions"]["basic_sc"])

    LOGGER.info("Creating servient with TD catalogue on: {}".format(CATALOGUE_PORT))
    servient = Servient(catalogue_port=CATALOGUE_PORT)
    #servient.add_server(http_server)
    servient.add_server(coap_server)

    credentials_dict = {
        TD["title"]: {
            "username": "user",
            "password": "pass"
        }
    }
    servient.add_credentials(credentials_dict)

    LOGGER.info("Starting servient")
    wot = await servient.start()

    LOGGER.info("Exposing and configuring Thing")

    # Produce the Thing from Thing Description
    exposed_thing = wot.produce(json.dumps(TD))

    # Initialize the property value
    await exposed_thing.properties["dummy"].write(42)

    exposed_thing.expose()

    new_prop_name = "new_property"
    new_prop_dict = {
        "type": "string",
        "observable": True
    }
    exposed_thing.add_property(new_prop_name, new_prop_dict, value="initial string value")
    servient.refresh_forms()

    LOGGER.info("URL of Thing is at: {}".format(exposed_thing.thing.url_name))

    LOGGER.info(f'{TD["title"]} is ready')


if __name__ == "__main__":
    LOGGER.info("Starting loop")
    loop = asyncio.new_event_loop()
    loop.create_task(main())
    loop.run_forever()
