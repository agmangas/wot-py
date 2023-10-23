#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
import os

import aiomqtt

from wotpy.protocols.mqtt.utils import MQTTBrokerURL

ENV_BROKER_URL = "WOTPY_TESTS_MQTT_BROKER_URL"
BROKER_SKIP_REASON = "The test MQTT broker is offline"


def get_test_broker_url():
    """Returns the MQTT broker URL defined in the environment."""

    return os.environ.get(ENV_BROKER_URL, None)


async def is_test_broker_online_async():
    broker_url = get_test_broker_url()

    if not broker_url:
        logging.warning("Undefined MQTT broker URL")
        return False

    mqtt_broker_url = MQTTBrokerURL.from_url(broker_url)

    client_config = {
        "hostname": mqtt_broker_url.host,
        "port": mqtt_broker_url.port,
        "username": mqtt_broker_url.username,
        "password": mqtt_broker_url.password,
    }

    try:
        async with aiomqtt.Client(**client_config) as client:
            logging.debug("Connected to test MQTT broker: {}".format(client_config))
            assert client
            return True
    except Exception as ex:
        logging.debug("Test MQTT broker connection error: {}".format(ex))
        logging.warning(
            "Couldn't connect to the test MQTT broker. "
            "Please check the {} variable".format(ENV_BROKER_URL)
        )
        return False


def is_test_broker_online():
    return asyncio.run(is_test_broker_online_async())
