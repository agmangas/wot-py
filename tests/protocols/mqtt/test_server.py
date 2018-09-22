#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid
# noinspection PyCompatibility
from asyncio import TimeoutError

import pytest
import tornado.gen
import tornado.ioloop
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_2

from tests.protocols.mqtt.broker import is_test_broker_online, BROKER_SKIP_REASON, get_test_broker_url
from wotpy.protocols.mqtt.enums import MQTTWoTTopics
from wotpy.protocols.mqtt.server import MQTTServer

pytestmark = pytest.mark.skipif(is_test_broker_online() is False, reason=BROKER_SKIP_REASON)


def test_start_stop():
    """The MQTT server may be started and stopped."""

    broker_url = get_test_broker_url()
    mqtt_server = MQTTServer(broker_url=broker_url)

    @tornado.gen.coroutine
    def ping(timeout=None):
        try:
            hbmqtt_client = MQTTClient()
            yield hbmqtt_client.connect(broker_url)
            yield hbmqtt_client.subscribe([(MQTTWoTTopics.PONG, QOS_2)])
            bytes_payload = bytes(uuid.uuid4().hex, "utf8")
            yield hbmqtt_client.publish(MQTTWoTTopics.PING, bytes_payload, qos=QOS_2)
            message = yield hbmqtt_client.deliver_message(timeout=timeout)
            assert message.data == bytes_payload
            yield hbmqtt_client.disconnect()
        except TimeoutError:
            raise tornado.gen.Return(False)

        raise tornado.gen.Return(True)

    default_timeout = 1.0

    @tornado.gen.coroutine
    def test_coroutine():
        assert not (yield ping(default_timeout))

        yield mqtt_server.start()

        assert (yield ping())
        assert (yield ping())

        yield mqtt_server.stop()
        yield mqtt_server.start()
        yield mqtt_server.stop()

        assert not (yield ping(default_timeout))

        yield mqtt_server.stop()
        yield mqtt_server.start()

        assert (yield ping())

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
