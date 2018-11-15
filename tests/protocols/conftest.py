#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import uuid

import pytest
import tornado.gen
import tornado.ioloop

from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.support import is_coap_supported, is_mqtt_supported
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

    if is_mqtt_supported():
        from wotpy.protocols.mqtt.server import MQTTServer
        from tests.protocols.mqtt.broker import get_test_broker_url, is_test_broker_online
        if is_test_broker_online():
            mqtt_server = MQTTServer(broker_url=get_test_broker_url())
            servient.add_server(mqtt_server)

    @tornado.gen.coroutine
    def start():
        raise tornado.gen.Return((yield servient.start()))

    wot = tornado.ioloop.IOLoop.current().run_sync(start)

    td_dict = {
        "id": uuid.uuid4().urn,
        "name": uuid.uuid4().hex,
        "properties": {
            uuid.uuid4().hex: {
                "observable": True,
                "type": "string"
            }
        }
    }

    td = ThingDescription(td_dict)

    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    yield servient

    @tornado.gen.coroutine
    def shutdown():
        yield servient.shutdown()

    tornado.ioloop.IOLoop.current().run_sync(shutdown)
