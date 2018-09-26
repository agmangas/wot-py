#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT clients to handle PING messages published on the MQTT server's broker.
"""

import tornado.gen
from hbmqtt.mqtt.constants import QOS_1


class PingMQTTHandler(object):
    """MQTT handler for PING requests."""

    TOPIC_PING = "/wotpy/ping"
    TOPIC_PONG = "/wotpy/pong"

    def __init__(self, mqtt_server, qos=QOS_1):
        self._mqtt_server = mqtt_server
        self._qos = qos

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return [(self.TOPIC_PING, self._qos)]

    @tornado.gen.coroutine
    def handle_message(self, client, msg):
        """Called each time the runner receives a message for one of the handler topics.
        Publishes a message in the PONG topic with the same
        payload as the one received in the PING topic."""

        yield client.publish(self.TOPIC_PONG, msg.data, qos=self._qos)

    @tornado.gen.coroutine
    def init(self):
        """Initializes the MQTT handler.
        Called when the MQTT runner starts."""

        pass

    @tornado.gen.coroutine
    def teardown(self):
        """Destroys the MQTT handler.
        Called when the MQTT runner stops."""

        pass
