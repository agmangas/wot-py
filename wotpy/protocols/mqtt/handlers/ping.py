#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT handler for PING requests published on the MQTT broker.
"""

from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler


class PingMQTTHandler(BaseMQTTHandler):
    """MQTT handler for PING requests published on the MQTT broker."""

    def __init__(self, mqtt_server, qos=1):
        super(PingMQTTHandler, self).__init__(mqtt_server)
        self._qos = qos

    @property
    def topic_ping(self):
        """Ping topic."""

        return "{}/ping".format(self.servient_id)

    @property
    def topic_pong(self):
        """Pong topic."""

        return "{}/pong".format(self.servient_id)

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return [(self.topic_ping, self._qos)]

    async def handle_message(self, msg):
        """Publishes a message in the PONG topic with the
        same payload as the one received in the PING topic."""

        await self.queue.put(
            {"topic": self.topic_pong, "data": msg.payload, "qos": self._qos}
        )
