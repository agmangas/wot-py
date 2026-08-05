#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

import os
import ssl
import tempfile
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from faker import Faker
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from tests.utils import find_free_port
from tests.protocols.zenoh.router import (get_test_router_url,
                                          is_test_router_online)
from wotpy.protocols.zenoh.server import ZenohServer
from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.support import is_coap_supported, is_mqtt_supported
from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription


@pytest_asyncio.fixture
async def all_protocols_servient():
    """Returns a Servient configured to use all available protocol bindings."""

    servient = Servient(catalogue_port=None)

    http_port = find_free_port()
    http_server = HTTPServer(port=http_port)
    servient.add_server(http_server)

    ws_port = find_free_port()
    ws_server = WebsocketServer(port=ws_port)
    servient.add_server(ws_server)

    if await is_test_router_online():
        zenoh_server = ZenohServer(router_url=get_test_router_url())
        servient.add_server(zenoh_server)

    if is_coap_supported():
        from wotpy.protocols.coap.server import CoAPServer

        coap_port = find_free_port()
        coap_server = CoAPServer(port=coap_port)
        servient.add_server(coap_server)

    if is_mqtt_supported():
        from tests.protocols.mqtt.broker import (
            get_test_broker_url,
            is_test_broker_online
        )
        from wotpy.protocols.mqtt.server import MQTTServer

        if await is_test_broker_online():
            mqtt_server = MQTTServer(broker_url=get_test_broker_url())
            servient.add_server(mqtt_server)

    wot = await servient.start()

    property_name = uuid.uuid4().hex
    title = uuid.uuid4().hex
    td_dict = {
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": uuid.uuid4().urn,
        "title": title,
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc",
        "properties": {
            property_name: {
                "observable": True,
                "type": "string"
            }
        }
    }

    td = ThingDescription(td_dict)

    exposed_thing = wot.produce(td.to_str())
    exposed_thing.expose()

    yield servient

    await servient.shutdown()


@pytest.fixture
def self_signed_ssl_context():
    """Returns a self-signed SSL certificate using cryptography."""

    base_dir = tempfile.gettempdir()
    
    certfile = os.path.join(base_dir, f"{uuid.uuid4().hex}.pem")
    keyfile = os.path.join(base_dir, f"{uuid.uuid4().hex}.pem")

    fake = Faker()

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "ES"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, fake.state()),
        x509.NameAttribute(NameOID.LOCALITY_NAME, fake.city()),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, fake.company()),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, fake.company_suffix()),
        x509.NameAttribute(NameOID.COMMON_NAME, fake.domain_name()),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(hours=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA384())
    )

    with open(keyfile, "wb") as fh:
        fh.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )

    with open(certfile, "wb") as fh:
        fh.write(cert.public_bytes(serialization.Encoding.PEM))

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)

    try:
        yield ssl_context
    finally:
        os.remove(certfile)
        os.remove(keyfile)
