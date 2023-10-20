#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that implements the MQTT server (broker).
"""

import asyncio

from slugify import slugify

from wotpy.codecs.enums import MediaTypes
from wotpy.protocols.enums import InteractionVerbs, Protocols
from wotpy.protocols.mqtt.handlers.action import ActionMQTTHandler
from wotpy.protocols.mqtt.handlers.event import EventMQTTHandler
from wotpy.protocols.mqtt.handlers.ping import PingMQTTHandler
from wotpy.protocols.mqtt.handlers.property import PropertyMQTTHandler
from wotpy.protocols.mqtt.runner import MQTTHandlerRunner
from wotpy.protocols.server import BaseProtocolServer
from wotpy.wot.enums import InteractionTypes
from wotpy.wot.form import Form


class MQTTServer(BaseProtocolServer):
    """MQTT binding server implementation."""

    DEFAULT_SERVIENT_ID = "wotpy"

    def __init__(
        self,
        broker_url,
        property_callback_ms=None,
        event_callback_ms=None,
        servient_id=None,
    ):
        super(MQTTServer, self).__init__(port=None)
        self._broker_url = broker_url
        self._server_lock = asyncio.Lock()
        self._servient_id = servient_id

        def build_runner(handler):
            return MQTTHandlerRunner(broker_url=self._broker_url, mqtt_handler=handler)

        self._handler_runners = [
            build_runner(PingMQTTHandler(mqtt_server=self)),
            build_runner(
                PropertyMQTTHandler(mqtt_server=self, callback_ms=property_callback_ms)
            ),
            build_runner(
                EventMQTTHandler(mqtt_server=self, callback_ms=event_callback_ms)
            ),
            build_runner(ActionMQTTHandler(mqtt_server=self)),
        ]

    @property
    def servient_id(self):
        """Servient ID that is used to avoid topic collisions
        øwhen multiple Servients are connected to the same broker."""

        return (
            slugify(self._servient_id)
            if self._servient_id
            else self.DEFAULT_SERVIENT_ID
        )

    @property
    def protocol(self):
        """Protocol of this server instance.
        A member of the Protocols enum."""

        return Protocols.MQTT

    def _build_forms_property(self, proprty):
        """Builds and returns the MQTT Form instances for the given Property interaction."""

        href_rw = "{}/{}/property/requests/{}/{}".format(
            self._broker_url.rstrip("/"),
            self.servient_id,
            proprty.thing.url_name,
            proprty.url_name,
        )

        form_read = Form(
            interaction=proprty,
            protocol=self.protocol,
            href=href_rw,
            content_type=MediaTypes.JSON,
            op=InteractionVerbs.READ_PROPERTY,
        )

        form_write = Form(
            interaction=proprty,
            protocol=self.protocol,
            href=href_rw,
            content_type=MediaTypes.JSON,
            op=InteractionVerbs.WRITE_PROPERTY,
        )

        href_observe = "{}/{}/property/updates/{}/{}".format(
            self._broker_url.rstrip("/"),
            self.servient_id,
            proprty.thing.url_name,
            proprty.url_name,
        )

        form_observe = Form(
            interaction=proprty,
            protocol=self.protocol,
            href=href_observe,
            content_type=MediaTypes.JSON,
            op=InteractionVerbs.OBSERVE_PROPERTY,
        )

        return [form_read, form_write, form_observe]

    def _build_forms_action(self, action):
        """Builds and returns the MQTT Form instances for the given Action interaction."""

        href = "{}/{}/action/invocation/{}/{}".format(
            self._broker_url.rstrip("/"),
            self.servient_id,
            action.thing.url_name,
            action.url_name,
        )

        form = Form(
            interaction=action,
            protocol=self.protocol,
            href=href,
            content_type=MediaTypes.JSON,
            op=InteractionVerbs.INVOKE_ACTION,
        )

        return [form]

    def _build_forms_event(self, event):
        """Builds and returns the MQTT Form instances for the given Event interaction."""

        href = "{}/{}/event/{}/{}".format(
            self._broker_url.rstrip("/"),
            self.servient_id,
            event.thing.url_name,
            event.url_name,
        )

        form = Form(
            interaction=event,
            protocol=self.protocol,
            href=href,
            content_type=MediaTypes.JSON,
            op=InteractionVerbs.SUBSCRIBE_EVENT,
        )

        return [form]

    def build_forms(self, hostname, interaction):
        """Builds and returns a list with all Forms that are
        linked to this server for the given Interaction."""

        intrct_type_map = {
            InteractionTypes.PROPERTY: self._build_forms_property,
            InteractionTypes.ACTION: self._build_forms_action,
            InteractionTypes.EVENT: self._build_forms_event,
        }

        if interaction.interaction_type not in intrct_type_map:
            raise ValueError("Unsupported interaction")

        return intrct_type_map[interaction.interaction_type](interaction)

    def build_base_url(self, hostname, thing):
        """Returns the base URL for the given Thing in the context of this server."""

        return self._broker_url

    async def start(self):
        """Starts the MQTT broker and all the MQTT clients
        that handle the WoT clients requests."""

        async with self._server_lock:
            await asyncio.gather(*[runner.start() for runner in self._handler_runners])

    async def stop(self):
        """Stops the MQTT broker and the MQTT clients."""

        async with self._server_lock:
            await asyncio.gather(*[runner.stop() for runner in self._handler_runners])
