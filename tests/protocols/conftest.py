#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import uuid

import pytest

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.support import is_coap_supported
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.description import ThingDescription
from wotpy.wot.servient import Servient


@pytest.fixture
def all_protocols_servient():
    """Returns a Servient configured to use all available protocol bindings."""

    servient = Servient()

    port_choices = list(range(20000, 40000))

    def pop_random_port():
        pop_idx = random.randint(0, len(port_choices) - 1)
        return port_choices.pop(pop_idx)

    http_port = pop_random_port()
    http_server = HTTPServer(port=http_port)
    servient.add_server(http_server)

    ws_port = pop_random_port()
    ws_server = WebsocketServer(port=ws_port)
    servient.add_server(ws_server)

    if is_coap_supported():
        from wotpy.protocols.coap.server import CoAPServer
        coap_port = pop_random_port()
        coap_server = CoAPServer(port=coap_port)
        servient.add_server(coap_server)

    wot = servient.start()

    td_dict = {
        "id": uuid.uuid4().urn,
        "name": uuid.uuid4().hex,
        "properties": {
            uuid.uuid4().hex: {
                "writable": True,
                "observable": True,
                "type": "string"
            }
        }
    }

    td = ThingDescription(td_dict)

    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    return servient
