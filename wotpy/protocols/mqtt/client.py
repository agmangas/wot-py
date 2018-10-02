#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the MQTT protocol.
"""

import json
import uuid

import hbmqtt.client
import tornado.gen
from hbmqtt.mqtt.constants import QOS_0
from six.moves.urllib import parse

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.enums import Protocols
from wotpy.protocols.exceptions import FormNotFoundException
from wotpy.protocols.mqtt.enums import MQTTSchemes
from wotpy.protocols.mqtt.handlers.action import ActionMQTTHandler
from wotpy.protocols.utils import is_scheme_form


class MQTTClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the MQTT protocol."""

    @classmethod
    def _pick_mqtt_href(cls, td, forms, rel=None):
        """Picks the most appropriate MQTT form href from the given list of forms."""

        def is_rel_form(form):
            try:
                return rel is None or rel == form.rel or rel in form.rel
            except TypeError:
                return False

        return next((
            form.href for form in forms
            if is_scheme_form(form, td.base, MQTTSchemes.MQTT) and is_rel_form(form)
        ), None)

    @classmethod
    def _parse_href(cls, href):
        """Takes an MQTT form href and returns
        the MQTT broker URL and the topic separately."""

        parsed_href = parse.urlparse(href)
        assert parsed_href.scheme and parsed_href.netloc and parsed_href.path

        return {
            "broker_url": "{}://{}".format(parsed_href.scheme, parsed_href.netloc),
            "topic": parsed_href.path.lstrip("/").rstrip("/")
        }

    @property
    def protocol(self):
        """Protocol of this client instance.
        A member of the Protocols enum."""

        return Protocols.MQTT

    def is_supported_interaction(self, td, name):
        """Returns True if the any of the Forms for the Interaction
        with the given name is supported in this Protocol Binding client."""

        forms = td.get_forms(name)

        forms_mqtt = [
            form for form in forms
            if is_scheme_form(form, td.base, MQTTSchemes.list())
        ]

        return len(forms_mqtt) > 0

    @tornado.gen.coroutine
    def invoke_action(self, td, name, input_value):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        href = self._pick_mqtt_href(td, td.get_action_forms(name))

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)

        topic_invoke = parsed_href["topic"]
        topic_result = ActionMQTTHandler.to_result_topic(topic_invoke)

        hbmqtt_client = hbmqtt.client.MQTTClient()
        yield hbmqtt_client.connect(parsed_href["broker_url"])
        yield hbmqtt_client.subscribe([(topic_result, QOS_0)])

        data = {
            "id": uuid.uuid4().hex,
            "input": input_value
        }

        input_payload = json.dumps(data).encode()

        yield hbmqtt_client.publish(topic_invoke, input_payload, qos=QOS_0)

        while True:
            msg = yield hbmqtt_client.deliver_message()
            msg_data = json.loads(msg.data.decode())

            if msg_data.get("id") != data.get("id"):
                continue

            if msg_data.get("error", None) is not None:
                raise Exception(msg_data.get("error"))
            else:
                raise tornado.gen.Return(msg_data.get("result"))

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        raise NotImplementedError

    @tornado.gen.coroutine
    def read_property(self, td, name):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        raise NotImplementedError

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        raise NotImplementedError

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
