#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyCompatibility
from asyncio import TimeoutError

import pytest
import tornado.gen
import tornado.ioloop
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_2

from wotpy.protocols.mqtt.enums import MQTTWoTTopics
from wotpy.protocols.mqtt.server import MQTTServer


@pytest.mark.skip(reason="Too slow. Unstable (relies on sleeps).")
@pytest.mark.flaky(reruns=5)
def test_start_stop():
    """"""

    broker_url = "mqtt://localhost"
    mqtt_server = MQTTServer(broker_url=broker_url)

    sleep_secs = 0.5

    @tornado.gen.coroutine
    def ping():
        try:
            hbmqtt_client = MQTTClient()
            yield hbmqtt_client.connect(broker_url)
            yield hbmqtt_client.subscribe([(MQTTWoTTopics.PONG, QOS_2)])
            yield hbmqtt_client.publish(MQTTWoTTopics.PING, b"PING", qos=QOS_2)
            message = yield hbmqtt_client.deliver_message(timeout=0.1)
            assert message.data
            yield hbmqtt_client.disconnect()
        except (Exception, TimeoutError):
            raise tornado.gen.Return(False)

        raise tornado.gen.Return(True)

    @tornado.gen.coroutine
    def test_coroutine():
        assert not (yield ping())

        mqtt_server.start()
        yield tornado.gen.sleep(sleep_secs)

        assert (yield ping())
        assert (yield ping())

        mqtt_server.stop()
        yield tornado.gen.sleep(sleep_secs)

        assert not (yield ping())

        mqtt_server.stop()
        yield tornado.gen.sleep(sleep_secs)

        mqtt_server.start()
        yield tornado.gen.sleep(sleep_secs)

        assert (yield ping())

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
