#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT clients to handle PING messages published on the MQTT server's broker.
"""

import tornado.gen
from hbmqtt.mqtt.constants import QOS_1

from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler


class PingMQTTHandler(BaseMQTTHandler):
    """MQTT handler for PING requests."""

    TOPIC_PING = "/wotpy/ping"
    TOPIC_PONG = "/wotpy/pong"

    def __init__(self, mqtt_server, qos=QOS_1):
        super(PingMQTTHandler, self).__init__(mqtt_server)
        self._qos = qos

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return [(self.TOPIC_PING, self._qos)]

    @tornado.gen.coroutine
    def handle_message(self, msg):
        """Publishes a message in the PONG topic with the
        same payload as the one received in the PING topic."""

        yield self.queue.put({
            "topic": self.TOPIC_PONG,
            "data": msg.data,
            "qos": self._qos
        })
