#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        "bearer_sc":{
            "scheme":"bearer"
        }
    },
    "security": "bearer_sc",
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
    LOGGER.info("Creating HTTP server on: {}".format(HTTP_PORT))
    http_server = HTTPServer(
        port=HTTP_PORT,
        security_scheme=TD["securityDefinitions"]["bearer_sc"])

    #LOGGER.info("Creating CoAP server on: {}".format(COAP_PORT))
    #coap_server = CoAPServer(port=COAP_PORT)

    LOGGER.info("Creating servient with TD catalogue on: {}".format(CATALOGUE_PORT))
    servient = Servient(catalogue_port=CATALOGUE_PORT)
    servient.add_server(http_server)
    #servient.add_server(coap_server)

    credentials_dict = {
        TD["title"]: {
            "token": "jg0ksz4nug1yf0ayi8ohf"
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
