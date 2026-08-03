#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Zenoh handler for PING requests published on the Zenoh router.
"""

from wotpy.protocols.zenoh.handlers.base import BaseZenohHandler


class PingZenohHandler(BaseZenohHandler):
    """Zenoh handler for PING requests published on the Zenoh broker."""

    def __init__(self, zenoh_server):
        super().__init__(zenoh_server)

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
        """List of topics that this Zenoh handler wants to subscribe to."""

        return [(self.topic_ping)]

    async def handle_message(self, sample):
        """Publishes a message in the PONG topic with the
        same payload as the one received in the PING topic."""

        return await self.queue.put({
            "topic": self.topic_pong,
            "data": sample.payload.to_string()
        })
