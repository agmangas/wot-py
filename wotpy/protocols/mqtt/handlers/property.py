#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT clients that expose Property verbs.
"""

import json
from json import JSONDecodeError

import six
import tornado.gen
import tornado.ioloop
from hbmqtt.mqtt.constants import QOS_0, QOS_2
from tornado.queues import QueueFull

from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler
from wotpy.utils.serialization import to_json_obj


class PropertyMQTTHandler(BaseMQTTHandler):
    """MQTT handler that responds to Property reads, writes and update subscriptions."""

    KEY_ACTION = "action"
    KEY_VALUE = "value"
    ACTION_READ = "read"
    ACTION_WRITE = "write"
    TOPIC_PROPERTY_WILDCARD = "property/requests/#"
    DEFAULT_CALLBACK_MS = 2000
    DEFAULT_JITTER = 0.2

    def __init__(self, mqtt_server, qos_observe=QOS_0, qos_rw=QOS_2, callback_ms=None):
        super(PropertyMQTTHandler, self).__init__(mqtt_server)

        callback_ms = self.DEFAULT_CALLBACK_MS if callback_ms is None else callback_ms

        self._qos_observe = qos_observe
        self._qos_rw = qos_rw
        self._callback_ms = callback_ms
        self._subs = {}

        self._periodic_refresh_subs = tornado.ioloop.PeriodicCallback(
            self._refresh_subs, self._callback_ms, jitter=self.DEFAULT_JITTER)

    @classmethod
    def build_property_requests_topic(cls, thing, prop):
        """Returns the MQTT topic for Property requests."""

        topic = "property/requests/{}/{}".format(thing.url_name, prop.url_name)
        assert cls.TOPIC_PROPERTY_WILDCARD.replace("#", "") in topic
        return topic

    @classmethod
    def build_property_updates_topic(cls, thing, prop):
        """Returns the MQTT topic for Property updates."""

        return "property/updates/{}/{}".format(thing.url_name, prop.url_name)

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return [(self.TOPIC_PROPERTY_WILDCARD, self._qos_rw)]

    @tornado.gen.coroutine
    def handle_message(self, msg):
        """Listens to all Property request topics and responds to read and write requests."""

        try:
            parsed_msg = json.loads(msg.data.decode())
        except (JSONDecodeError, TypeError):
            return

        action = parsed_msg.get(self.KEY_ACTION, False)

        if not action or action not in [self.ACTION_WRITE, self.ACTION_READ]:
            return

        topic_split = msg.topic.split("/")

        splits_expected_len = len(self.TOPIC_PROPERTY_WILDCARD.split("/")) + 1

        if len(topic_split) != splits_expected_len:
            return

        thing_url_name, prop_url_name = topic_split[-2], topic_split[-1]

        try:
            exp_thing = next(
                item for item in self.mqtt_server.exposed_things
                if item.url_name == thing_url_name)

            prop = next(
                exp_thing.thing.properties[key] for key in exp_thing.thing.properties
                if exp_thing.thing.properties[key].url_name == prop_url_name)
        except StopIteration:
            return

        if action == self.ACTION_READ:
            value = yield exp_thing.properties[prop.name].read()
            topic = self.build_property_updates_topic(exp_thing.thing, prop)
            msg = self._build_update_message(topic, value)
            yield self.queue.put(msg)
        elif action == self.ACTION_WRITE and self.KEY_VALUE in parsed_msg:
            yield exp_thing.properties[prop.name].write(parsed_msg[self.KEY_VALUE])

    @tornado.gen.coroutine
    def init(self):
        """Initializes the MQTT handler.
        Called when the MQTT runner starts."""

        self._refresh_subs()
        self._periodic_refresh_subs.start()

        yield None

    @tornado.gen.coroutine
    def teardown(self):
        """Destroys the MQTT handler.
        Called when the MQTT runner stops."""

        self._periodic_refresh_subs.stop()

        for exp_thing in self._subs:
            self._dispose_exposed_thing_subs(exp_thing)

        yield None

    def _build_update_message(self, topic, value):
        """Builds an MQTT message to publish an update for a Property value."""

        return {
            "topic": topic,
            "data": json.dumps({"value": to_json_obj(value)}).encode(),
            "qos": self._qos_observe
        }

    def _dispose_exposed_thing_subs(self, exp_thing):
        """Disposes of all currently active subscriptions for the given ExposedThing."""

        if exp_thing not in self._subs:
            return

        for prop in self._subs[exp_thing]:
            self._subs[exp_thing][prop].dispose()

        self._subs.pop(exp_thing)

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

    def _refresh_exposed_thing_subs(self, exp_thing):
        """Refresh the subscriptions for the given ExposedThing."""

        if exp_thing not in self._subs:
            self._subs[exp_thing] = {}

        thing_subs = self._subs[exp_thing]

        props_expected = set(six.itervalues(exp_thing.thing.properties))
        props_current = set(thing_subs.keys())
        props_remove = props_current.difference(props_expected)

        for prop in props_remove:
            thing_subs[prop].dispose()
            thing_subs.pop(prop)

        props_new = [item for item in props_expected if item not in thing_subs]

        for prop in props_new:
            on_next = self._build_on_next(exp_thing, prop)
            thing_subs[prop] = exp_thing.properties[prop.name].subscribe(on_next)

    def _refresh_subs(self):
        """Refresh all subscriptions for the entire set of ExposedThings."""

        things_expected = set(self.mqtt_server.exposed_things)
        things_current = set(self._subs.keys())
        things_remove = things_current.difference(things_expected)

        for exp_thing in things_remove:
            self._dispose_exposed_thing_subs(exp_thing)

        for exp_thing in things_expected:
            self._refresh_exposed_thing_subs(exp_thing)
