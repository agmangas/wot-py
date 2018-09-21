#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT clients to handle PING messages published on the MQTT server's broker.
"""

import tornado.gen
from hbmqtt.mqtt.constants import QOS_0

from wotpy.protocols.mqtt.enums import MQTTWoTTopics
from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler


class PingMQTTHandler(BaseMQTTHandler):
    """"""

    def __init__(self, broker_url, qos=QOS_0, timeout_deliver_secs=1.0):
        """"""

        self._qos = qos

        topics = [(MQTTWoTTopics.PING, self._qos)]

        super(PingMQTTHandler, self).__init__(
            broker_url, self.handle_message, topics,
            timeout_deliver_secs=timeout_deliver_secs)

    # noinspection PyUnusedLocal
    @tornado.gen.coroutine
    def handle_message(self, client, msg):
        """"""

        yield client.publish(MQTTWoTTopics.PONG, b"PONG", qos=self._qos)
