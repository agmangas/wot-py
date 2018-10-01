#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT handler for Event subscriptions.
"""

import json
import time

import six
import tornado.gen
import tornado.ioloop
from hbmqtt.mqtt.constants import QOS_0
from tornado.queues import QueueFull

from wotpy.protocols.mqtt.handlers.base import BaseMQTTHandler
from wotpy.utils.serialization import to_json_obj


class EventMQTTHandler(BaseMQTTHandler):
    """MQTT handler for Event subscriptions."""

    DEFAULT_CALLBACK_MS = 2000
    DEFAULT_JITTER = 0.2

    def __init__(self, mqtt_server, qos=QOS_0, callback_ms=None):
        super(EventMQTTHandler, self).__init__(mqtt_server)

        callback_ms = self.DEFAULT_CALLBACK_MS if callback_ms is None else callback_ms

        self._qos = qos
        self._callback_ms = callback_ms
        self._subs = {}

        self._periodic_refresh_subs = tornado.ioloop.PeriodicCallback(
            self._refresh_subs, self._callback_ms, jitter=self.DEFAULT_JITTER)

    @classmethod
    def build_event_topic(cls, thing, event):
        """Returns the MQTT topic for Event emissions."""

        return "event/{}/{}".format(thing.url_name, event.url_name)

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

        for exp_thing in list(six.iterkeys(self._subs)):
            self._dispose_exposed_thing_subs(exp_thing)

        yield None

    def _dispose_exposed_thing_subs(self, exp_thing):
        """Disposes of all currently active subscriptions for the given ExposedThing."""

        if exp_thing not in self._subs:
            return

        for key in self._subs[exp_thing]:
            self._subs[exp_thing][key].dispose()

        self._subs.pop(exp_thing)

    def _build_on_next(self, exp_thing, event):
        """Builds the on_next function to use when subscribing to the given Event."""

        topic = self.build_event_topic(exp_thing, event)

        def on_next(item):
            try:
                msg = {
                    "topic": topic,
                    "data": json.dumps({
                        "name": item.name,
                        "data": to_json_obj(item.data),
                        "time": int(time.time() * 1000)
                    }).encode(),
                    "qos": self._qos
                }

                self.queue.put_nowait(msg)
            except QueueFull:
                pass

        return on_next

    def _refresh_exposed_thing_subs(self, exp_thing):
        """Refresh the subscriptions for the given ExposedThing."""

        if exp_thing not in self._subs:
            self._subs[exp_thing] = {}

        thing_subs = self._subs[exp_thing]

        events_expected = set(six.itervalues(exp_thing.thing.events))
        events_current = set(thing_subs.keys())
        events_remove = events_current.difference(events_expected)

        for event in events_remove:
            thing_subs[event].dispose()
            thing_subs.pop(event)

        events_new = [item for item in events_expected if item not in thing_subs]

        for event in events_new:
            on_next = self._build_on_next(exp_thing, event)
            thing_subs[event] = exp_thing.events[event.name].subscribe(on_next)

    def _refresh_subs(self):
        """Refresh all subscriptions for the entire set of ExposedThings."""

        things_expected = set(self.mqtt_server.exposed_things)
        things_current = set(self._subs.keys())
        things_remove = things_current.difference(things_expected)

        for exp_thing in things_remove:
            self._dispose_exposed_thing_subs(exp_thing)

        for exp_thing in things_expected:
            self._refresh_exposed_thing_subs(exp_thing)
