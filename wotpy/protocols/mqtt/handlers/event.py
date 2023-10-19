#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT handler for Event subscriptions.
"""

import asyncio
import json
import time

import tornado.ioloop

from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler
from wotpy.protocols.mqtt.handlers.subs import InteractionsSubscriber
from wotpy.utils.utils import to_json_obj
from wotpy.wot.enums import InteractionTypes


class EventMQTTHandler(BaseMQTTHandler):
    """MQTT handler for Event subscriptions."""

    DEFAULT_CALLBACK_MS = 2000
    DEFAULT_JITTER = 0.2

    def __init__(self, mqtt_server, qos=0, callback_ms=None):
        super(EventMQTTHandler, self).__init__(mqtt_server)

        callback_ms = self.DEFAULT_CALLBACK_MS if callback_ms is None else callback_ms

        self._qos = qos
        self._callback_ms = callback_ms
        self._subs = {}

        self._interaction_subscriber = InteractionsSubscriber(
            interaction_type=InteractionTypes.EVENT,
            server=self.mqtt_server,
            on_next_builder=self._build_on_next,
        )

        async def refresh_subs():
            self._interaction_subscriber.refresh()

        self._periodic_refresh_subs = tornado.ioloop.PeriodicCallback(
            refresh_subs, self._callback_ms, jitter=self.DEFAULT_JITTER
        )

    def build_event_topic(self, thing, event):
        """Returns the MQTT topic for Event emissions."""

        return "{}/event/{}/{}".format(self.servient_id, thing.url_name, event.url_name)

    async def init(self):
        """Initializes the MQTT handler.
        Called when the MQTT runner starts."""

        self._interaction_subscriber.refresh()
        self._periodic_refresh_subs.start()

    async def teardown(self):
        """Destroys the MQTT handler.
        Called when the MQTT runner stops."""

        self._periodic_refresh_subs.stop()
        self._interaction_subscriber.dispose()

    def _build_on_next(self, exp_thing, event):
        """Builds the on_next function to use when subscribing to the given Event."""

        topic = self.build_event_topic(exp_thing, event)

        def on_next(item):
            try:
                data = {
                    "name": item.name,
                    "data": to_json_obj(item.data),
                    "timestamp": int(time.time() * 1000),
                }

                self.queue.put_nowait(
                    {
                        "topic": topic,
                        "data": json.dumps(data).encode(),
                        "qos": self._qos,
                    }
                )
            except asyncio.QueueFull:
                pass

        return on_next
