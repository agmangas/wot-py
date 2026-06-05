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
