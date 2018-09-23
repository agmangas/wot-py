#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the MQTT server (broker).
"""

import tornado.gen
import tornado.ioloop
import tornado.locks

from wotpy.protocols.enums import Protocols
from wotpy.protocols.mqtt.enums import MQTTSchemes
from wotpy.protocols.mqtt.handlers.ping import PingMQTTHandler
from wotpy.protocols.server import BaseProtocolServer


class MQTTServer(BaseProtocolServer):
    """MQTT binding server implementation."""

    def __init__(self, broker_url):
        super(MQTTServer, self).__init__(port=None)
        self._broker_url = broker_url
        self._server_lock = tornado.locks.Lock()

        self._mqtt_handlers = [
            PingMQTTHandler(self._broker_url)
        ]

    @property
    def protocol(self):
        """Protocol of this server instance.
        A member of the Protocols enum."""

        return Protocols.MQTT

    @property
    def scheme(self):
        """Returns the URL scheme for this server."""

        return MQTTSchemes.MQTT

    def build_forms(self, hostname, interaction):
        """Builds and returns a list with all Forms that are
        linked to this server for the given Interaction."""

        return []

    def build_base_url(self, hostname, thing):
        """Returns the base URL for the given Thing in the context of this server."""

        if not self.exposed_thing_group.find_by_thing_id(thing.id):
            raise ValueError("Unknown Thing")

        return "{}://{}:{}/{}".format(
            self.scheme, hostname.rstrip("/").lstrip("/"),
            self.port, thing.url_name)

    @tornado.gen.coroutine
    def start(self):
        """Starts the MQTT broker and all the MQTT clients
        that handle the WoT clients requests."""

        with (yield self._server_lock.acquire()):
            yield [handler.connect() for handler in self._mqtt_handlers]
            yield [handler.start() for handler in self._mqtt_handlers]

    @tornado.gen.coroutine
    def stop(self):
        """Stops the MQTT broker and the MQTT clients."""

        with (yield self._server_lock.acquire()):
            yield [handler.stop() for handler in self._mqtt_handlers]
            yield [handler.disconnect() for handler in self._mqtt_handlers]
