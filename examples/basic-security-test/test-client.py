#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import asyncio
import logging

from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT
from wotpy.protocols.http.client import HTTPClient
from wotpy.protocols.coap.client import CoAPClient

logging.basicConfig()
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)


async def main():
    coap_client = CoAPClient()
    #http_client = HTTPClient()
    security_scheme_dict = {
        "scheme": "basic"
    }
    credentials_dict = {
        "username": "user",
        "password": "pass"
    }
    #http_client.set_security(security_scheme_dict, credentials_dict)
    coap_client.set_security(security_scheme_dict, credentials_dict)
    wot = WoT(servient=Servient(clients=[coap_client]))

    LOGGER.info("Clients: {}".format(wot.servient.clients))
    consumed_thing = await wot.consume_from_url("http://127.0.0.1:9090/test")

    LOGGER.info("Consumed Thing: {}".format(consumed_thing))
    result = await consumed_thing.read_property("dummy")
    print(result)
    new_property = await consumed_thing.read_property("new_property")
    print(new_property)


if __name__ == "__main__":
    asyncio.run(main())
