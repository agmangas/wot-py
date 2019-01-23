#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class for all MQTT handlers.
"""

import tornado.gen

from tornado.queues import Queue


class BaseMQTTHandler(object):
    """Base class for all MQTT handlers."""

    def __init__(self, mqtt_server):
        self._mqtt_server = mqtt_server
        self._queue = Queue()

    @property
    def servient_id(self):
        """Servient ID that is used to avoid topic collisions
        øwhen multiple Servients are connected to the same broker."""

        return self._mqtt_server.servient_id

    @property
    def mqtt_server(self):
        """MQTT server that contains this handler."""

        return self._mqtt_server

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return None

    @property
    def queue(self):
        """Asynchronous queue where the handler leaves messages
        that should be published later by the runner."""

        return self._queue

    @tornado.gen.coroutine
    def handle_message(self, msg):
        """Called each time the runner receives a message for one of the handler topics."""

        pass

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
