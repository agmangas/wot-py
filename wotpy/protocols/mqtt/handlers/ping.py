#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT clients to handle PING messages published on the MQTT server's broker.
"""

import tornado.gen
from hbmqtt.mqtt.constants import QOS_1

from wotpy.protocols.mqtt.enums import MQTTWoTTopics
from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler


class PingMQTTHandler(BaseMQTTHandler):
    """MQTT handler for PING requests."""

    def __init__(self, broker_url, qos=QOS_1, timeout_deliver_secs=None):
        self._qos = qos

        topics = [(MQTTWoTTopics.PING, self._qos)]

        kwargs = {}

        if timeout_deliver_secs is not None:
            kwargs.update({"timeout_deliver_secs": timeout_deliver_secs})

        super(PingMQTTHandler, self).__init__(broker_url, self.handle_message, topics, **kwargs)

    @tornado.gen.coroutine
    def handle_message(self, client, msg):
        """Publishes a message in the PONG topic with the
        same payload as the one received in the PING topic."""

        yield client.publish(MQTTWoTTopics.PONG, msg.data, qos=self._qos)
