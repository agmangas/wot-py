#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the MQTT protocol.
"""

import json
import uuid

import hbmqtt.client
import tornado.concurrent
import tornado.gen
import tornado.ioloop
from hbmqtt.mqtt.constants import QOS_0
from rx import Observable
from six.moves.urllib import parse

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.enums import Protocols, InteractionVerbs
from wotpy.protocols.exceptions import FormNotFoundException
from wotpy.protocols.mqtt.enums import MQTTSchemes
from wotpy.protocols.mqtt.handlers.action import ActionMQTTHandler
from wotpy.protocols.utils import is_scheme_form
from wotpy.wot.events import PropertyChangeEventInit, PropertyChangeEmittedEvent, EmittedEvent


class MQTTClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the MQTT protocol."""

    DEFAULT_DELIVER_TIMEOUT_SECS = 0.1

    def __init__(self, deliver_timeout_secs=DEFAULT_DELIVER_TIMEOUT_SECS, qos=QOS_0):
        self._deliver_timeout_secs = deliver_timeout_secs
        self._qos = qos

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

        client = hbmqtt.client.MQTTClient()

        try:
            yield client.connect(parsed_href["broker_url"])
            yield client.subscribe([(topic_result, self._qos)])

            data = {
                "id": uuid.uuid4().hex,
                "input": input_value
            }

            input_payload = json.dumps(data).encode()

            yield client.publish(topic_invoke, input_payload, qos=self._qos)

            while True:
                msg = yield client.deliver_message()
                msg_data = json.loads(msg.data.decode())

                if msg_data.get("id") != data.get("id"):
                    continue

                if msg_data.get("error", None) is not None:
                    raise Exception(msg_data.get("error"))
                else:
                    raise tornado.gen.Return(msg_data.get("result"))
        finally:
            try:
                yield client.disconnect()
            except AttributeError:
                pass

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        """Updates the value of a Property on a remote Thing.
        Due to the MQTT binding design this coroutine yields as soon as the write message has
        been published and will not wait for a custom write handler that yields to another coroutine
        Returns a Future."""

        forms = td.get_property_forms(name)

        href_write = self._pick_mqtt_href(td, forms, rel=InteractionVerbs.WRITE_PROPERTY)

        if href_write is None:
            raise FormNotFoundException()

        parsed_href_write = self._parse_href(href_write)

        client_write = hbmqtt.client.MQTTClient()

        try:
            yield client_write.connect(parsed_href_write["broker_url"])
            write_payload = json.dumps({"action": "write", "value": value}).encode()
            yield client_write.publish(parsed_href_write["topic"], write_payload, qos=self._qos)
        finally:
            try:
                yield client_write.disconnect()
            except AttributeError:
                pass

    @tornado.gen.coroutine
    def read_property(self, td, name):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        forms = td.get_property_forms(name)

        href_read = self._pick_mqtt_href(td, forms, rel=InteractionVerbs.READ_PROPERTY)
        href_obsv = self._pick_mqtt_href(td, forms, rel=InteractionVerbs.OBSERVE_PROPERTY)

        if href_read is None or href_obsv is None:
            raise FormNotFoundException()

        parsed_href_read = self._parse_href(href_read)
        parsed_href_obsv = self._parse_href(href_obsv)

        client_read = hbmqtt.client.MQTTClient()
        client_obsv = hbmqtt.client.MQTTClient()

        try:
            yield client_read.connect(parsed_href_read["broker_url"])
            yield client_obsv.connect(parsed_href_obsv["broker_url"])

            yield client_obsv.subscribe([(parsed_href_obsv["topic"], self._qos)])

            read_payload = json.dumps({"action": "read"}).encode()
            yield client_read.publish(parsed_href_read["topic"], read_payload, qos=self._qos)

            msg = yield client_obsv.deliver_message()
            msg_data = json.loads(msg.data.decode())

            raise tornado.gen.Return(msg_data.get("value"))
        finally:
            try:
                yield client_read.disconnect()
            except AttributeError:
                pass

            try:
                yield client_obsv.disconnect()
            except AttributeError:
                pass

    def _build_subscribe(self, broker_url, topic, next_item_builder):
        """Builds the subscribe function that should be passed when
        constructing an Observable to listen for messages on an MQTT topic."""

        def subscribe(observer):
            """Subscriber function that listens for MQTT messages
            on a given topic and passes them to the Observer."""

            state = {
                "active": True
            }

            client = hbmqtt.client.MQTTClient()

            def on_message(fut):
                is_timeout = fut and isinstance(fut.exception(), tornado.concurrent.futures.TimeoutError)

                if fut is not None and fut.exception() and not is_timeout:
                    observer.on_error(fut.exception())
                    return
                elif fut is not None and fut.exception() is None:
                    next_item = next_item_builder(fut.result())
                    if next_item is not None:
                        observer.on_next(next_item)

                if not state["active"]:
                    return

                timeout = self._deliver_timeout_secs
                fut_msg = tornado.gen.convert_yielded(client.deliver_message(timeout=timeout))
                tornado.concurrent.future_add_done_callback(fut_msg, on_message)

            def on_subscribe(fut):
                if fut.exception():
                    observer.on_error(fut.exception())
                    return

                on_message(None)

            def on_connect(fut):
                if fut.exception():
                    observer.on_error(fut.exception())
                    return

                topics = [(topic, self._qos)]
                fut_sub = tornado.gen.convert_yielded(client.subscribe(topics))
                tornado.concurrent.future_add_done_callback(fut_sub, on_subscribe)

            fut_con = tornado.gen.convert_yielded(client.connect(broker_url))
            tornado.concurrent.future_add_done_callback(fut_con, on_connect)

            def unsubscribe():
                """Disconnects from the MQTT broker and stops the message delivering loop."""

                @tornado.gen.coroutine
                def disconnect():
                    try:
                        yield client.disconnect()
                    except AttributeError:
                        pass

                tornado.ioloop.IOLoop.current().add_callback(disconnect)

                state["active"] = False

            return unsubscribe

        return subscribe

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        forms = td.get_property_forms(name)
        href = self._pick_mqtt_href(td, forms, rel=InteractionVerbs.OBSERVE_PROPERTY)

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)

        broker_url = parsed_href["broker_url"]
        topic = parsed_href["topic"]

        def next_item_builder(msg):
            try:
                msg_data = json.loads(msg.data.decode())
                msg_value = msg_data.get("value")
                init = PropertyChangeEventInit(name=name, value=msg_value)
                return PropertyChangeEmittedEvent(init=init)
            except (TypeError, ValueError, json.decoder.JSONDecodeError):
                return None

        subscribe = self._build_subscribe(
            broker_url=broker_url,
            topic=topic,
            next_item_builder=next_item_builder)

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        forms = td.get_event_forms(name)
        href = self._pick_mqtt_href(td, forms, rel=InteractionVerbs.SUBSCRIBE_EVENT)

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)

        broker_url = parsed_href["broker_url"]
        topic = parsed_href["topic"]

        def next_item_builder(msg):
            try:
                msg_data = json.loads(msg.data.decode())
                return EmittedEvent(init=msg_data.get("data"), name=name)
            except (TypeError, ValueError, json.decoder.JSONDecodeError):
                return None

        subscribe = self._build_subscribe(
            broker_url=broker_url,
            topic=topic,
            next_item_builder=next_item_builder)

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
