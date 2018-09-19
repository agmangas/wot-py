#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the MQTT server (broker).
"""

from wotpy.protocols.enums import Protocols
from wotpy.protocols.mqtt.enums import MQTTSchemes
from wotpy.protocols.server import BaseProtocolServer


class MQTTServer(BaseProtocolServer):
    """MQTT binding server implementation."""

    def __init__(self):
        super(MQTTServer, self).__init__(port=None)

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

    def start(self):
        """Starts the MQTT broker and all the MQTT clients
        that handle the WoT clients requests."""

        pass

    def stop(self):
        """Stops the MQTT broker and the MQTT clients."""

        pass
