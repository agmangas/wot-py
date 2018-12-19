#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ssl
import tempfile
import uuid

import pytest
import tornado.gen
import tornado.ioloop
from OpenSSL import crypto
from faker import Faker

from tests.utils import find_free_port
from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.support import is_coap_supported, is_mqtt_supported
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription


@pytest.fixture
def all_protocols_servient():
    """Returns a Servient configured to use all available protocol bindings."""

    servient = Servient(catalogue_port=None)

    http_port = find_free_port()
    http_server = HTTPServer(port=http_port)
    servient.add_server(http_server)

    ws_port = find_free_port()
    ws_server = WebsocketServer(port=ws_port)
    servient.add_server(ws_server)

    if is_coap_supported():
        from wotpy.protocols.coap.server import CoAPServer
        coap_port = find_free_port()
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


@pytest.fixture
def self_signed_ssl_context():
    """Returns a self-signed SSL certificate."""

    base_dir = tempfile.gettempdir()

    certfile = os.path.join(base_dir, "{}.pem".format(uuid.uuid4().hex))
    keyfile = os.path.join(base_dir, "{}.pem".format(uuid.uuid4().hex))

    pkey = crypto.PKey()
    pkey.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.get_subject().C = "ES"
    cert.get_subject().ST = Faker().pystr()
    cert.get_subject().L = Faker().pystr()
    cert.get_subject().O = Faker().pystr()
    cert.get_subject().OU = Faker().pystr()
    cert.get_subject().CN = Faker().pystr()
    cert.set_serial_number(Faker().pyint())
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(3600)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(pkey)
    # noinspection PyTypeChecker
    cert.sign(pkey, "sha384")

    with open(certfile, "wb") as fh:
        fh.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    with open(keyfile, "wb") as fh:
        fh.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, pkey))

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    yield ssl_context

    os.remove(certfile)
    os.remove(keyfile)
