#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT handler for Property reads, writes and subscriptions to value updates.
"""

import json
import time
from asyncio import QueueFull
from json import JSONDecodeError

import tornado.ioloop

from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler
from wotpy.protocols.mqtt.handlers.subs import InteractionsSubscriber
from wotpy.utils.utils import to_json_obj
from wotpy.wot.enums import InteractionTypes


class PropertyMQTTHandler(BaseMQTTHandler):
    """MQTT handler for Property reads, writes and subscriptions to value updates."""

    KEY_ACTION = "action"
    KEY_VALUE = "value"
    KEY_ACK = "ack"
    ACTION_READ = "read"
    ACTION_WRITE = "write"
    DEFAULT_CALLBACK_MS = 2000
    DEFAULT_JITTER = 0.2

    def __init__(self, mqtt_server, qos_observe=0, qos_rw=1, callback_ms=None):
        super(PropertyMQTTHandler, self).__init__(mqtt_server)

        callback_ms = self.DEFAULT_CALLBACK_MS if callback_ms is None else callback_ms

        self._qos_observe = qos_observe
        self._qos_rw = qos_rw
        self._callback_ms = callback_ms
        self._subs = {}

        self._interaction_subscriber = InteractionsSubscriber(
            interaction_type=InteractionTypes.PROPERTY,
            server=self.mqtt_server,
            on_next_builder=self._build_on_next,
        )

        async def refresh_subs():
            self._interaction_subscriber.refresh()

        self._periodic_refresh_subs = tornado.ioloop.PeriodicCallback(
            refresh_subs, self._callback_ms, jitter=self.DEFAULT_JITTER
        )

    @property
    def topic_wildcard_requests(self):
        """Wildcard topic to subscribe to all Property requests."""

        return "{}/property/requests/#".format(self.servient_id)

    def build_property_updates_topic(self, thing, prop):
        """Returns the MQTT topic for Property updates."""

        return "{}/property/updates/{}/{}".format(
            self.servient_id, thing.url_name, prop.url_name
        )

    @classmethod
    def to_write_ack_topic(cls, requests_topic):
        """Takes a Property requests topic and returns the related write ACK topic."""

        # ToDo: Ensure that topic is a str instead of an instance of aiomqtt.Topic
        try:
            topic_split = requests_topic.value.split("/")
        except Exception:
            topic_split = requests_topic.split("/")

        servient_id, thing_name, prop_name = (
            topic_split[-5],
            topic_split[-2],
            topic_split[-1],
        )

        return "{}/property/ack/{}/{}".format(servient_id, thing_name, prop_name)

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return [(self.topic_wildcard_requests, self._qos_rw)]

    async def handle_message(self, msg):
        """Listens to all Property request topics and responds to read and write requests."""

        try:
            parsed_msg = json.loads(msg.payload.decode())
        except (JSONDecodeError, TypeError):
            return

        action = parsed_msg.get(self.KEY_ACTION, False)

        if not action or action not in [self.ACTION_WRITE, self.ACTION_READ]:
            return

        topic_split = msg.topic.value.split("/")

        splits_expected_len = len(self.topic_wildcard_requests.split("/")) + 1

        if len(topic_split) != splits_expected_len:
            return

        thing_url_name, prop_url_name = topic_split[-2], topic_split[-1]

        try:
            exp_thing = next(
                item
                for item in self.mqtt_server.exposed_things
                if item.url_name == thing_url_name
            )

            prop = next(
                exp_thing.thing.properties[key]
                for key in exp_thing.thing.properties
                if exp_thing.thing.properties[key].url_name == prop_url_name
            )
        except StopIteration:
            return

        if action == self.ACTION_READ:
            value = await exp_thing.properties[prop.name].read()
            topic = self.build_property_updates_topic(exp_thing.thing, prop)
            update_msg = self._build_update_message(topic, value)
            await self.queue.put(update_msg)
        elif action == self.ACTION_WRITE and self.KEY_VALUE in parsed_msg:
            await exp_thing.properties[prop.name].write(parsed_msg[self.KEY_VALUE])
            await self.publish_write_ack(msg)

    async def publish_write_ack(self, msg):
        """Takes a Property write request message and publishes the related write ACK message."""

        try:
            parsed_msg = json.loads(msg.payload.decode())
        except (JSONDecodeError, TypeError):
            return

        action = parsed_msg.get(self.KEY_ACTION, None)
        ack_code = parsed_msg.get(self.KEY_ACK, None)

        if not action or not ack_code or action != self.ACTION_WRITE:
            return

        topic_ack = self.to_write_ack_topic(msg.topic)

        await self.queue.put(
            {
                "topic": topic_ack,
                "data": json.dumps({self.KEY_ACK: ack_code}).encode(),
                "qos": self._qos_rw,
            }
        )

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

    def _build_update_message(self, topic, value):
        """Builds an MQTT message to publish an update for a Property value."""

        now_ms = int(time.time() * 1000)

        return {
            "topic": topic,
            "data": json.dumps(
                {"value": to_json_obj(value), "timestamp": now_ms}
            ).encode(),
            "qos": self._qos_observe,
        }

    def _build_on_next(self, exp_thing, prop):
        """Builds the on_next function to use when subscribing to the given Property."""

        topic = self.build_property_updates_topic(exp_thing, prop)

        def on_next(item):
            try:
                msg = self._build_update_message(topic, item.data.value)
                self.queue.put_nowait(msg)
            except QueueFull:
                pass

        return on_next
