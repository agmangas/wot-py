#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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

import logging
import os

from amqtt.client import MQTTClient
try:
    from amqtt.client import ConnectError
except ImportError:
    from amqtt.client import ClientException as ConnectError

from wotpy.protocols.mqtt.enums import MQTTCodesACK

ENV_BROKER_URL = "WOTPY_TESTS_MQTT_BROKER_URL"
BROKER_SKIP_REASON = "The test MQTT broker is offline"


def get_test_broker_url():
    """Returns the MQTT broker URL defined in the environment."""

    return os.environ.get(ENV_BROKER_URL, None)


async def is_test_broker_online():
    """Returns True if the MQTT broker defined in the environment is online."""

    async def check_conn():
        broker_url = get_test_broker_url()

        if not broker_url:
            logging.warning("Undefined MQTT broker URL")
            return False

        try:
            amqtt_client = MQTTClient()
            ack_con = await amqtt_client.connect(broker_url)
            if ack_con != MQTTCodesACK.CON_OK:
                logging.warning("Error ACK on MQTT broker connection: {}".format(ack_con))
                return False
        except ConnectError as ex:
            logging.warning("MQTT broker connection error: {}".format(ex))
            return False

        return True

    conn_ok = await check_conn()

    if conn_ok is False:
        logging.warning(
            "Couldn't connect to the test MQTT broker. "
            "Please check the {} variable".format(ENV_BROKER_URL))

    return conn_ok
