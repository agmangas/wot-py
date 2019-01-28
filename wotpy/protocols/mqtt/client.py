#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the MQTT protocol.
"""

import asyncio
import datetime
import json
import logging
import time
import uuid
from json import JSONDecodeError

import hbmqtt.client
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.locks
from hbmqtt.mqtt.constants import QOS_0
from rx import Observable
from six.moves.urllib import parse

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.enums import Protocols, InteractionVerbs
from wotpy.protocols.exceptions import FormNotFoundException
from wotpy.protocols.mqtt.enums import MQTTSchemes
from wotpy.protocols.mqtt.handlers.action import ActionMQTTHandler
from wotpy.protocols.mqtt.handlers.property import PropertyMQTTHandler
from wotpy.protocols.utils import is_scheme_form
from wotpy.utils.utils import handle_observer_finalization
from wotpy.wot.events import PropertyChangeEventInit, PropertyChangeEmittedEvent, EmittedEvent


class MQTTClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the MQTT protocol."""

    DELIVER_TERMINATE_LOOP_SLEEP_SECS = 0.1
    SLEEP_SECS_DELIVER_ERR = 1.0

    def __init__(self, wait_on_write=True, qos=QOS_0,
                 deliver_timeout_secs=1, msg_wait_timeout_secs=5, msg_ttl_secs=15):
        self._wait_on_write = wait_on_write
        self._qos = qos
        self._deliver_timeout_secs = deliver_timeout_secs
        self._msg_wait_timeout_secs = msg_wait_timeout_secs
        self._msg_ttl_secs = msg_ttl_secs
        self._lock_client = tornado.locks.Lock()
        self._deliver_stop_events = {}
        self._client_ref_counter = {}
        self._msg_conditions = {}
        self._clients = {}
        self._messages = {}
        self._logr = logging.getLogger(__name__)

    def _build_deliver(self, broker_url):
        """Factory for functions to get messages delivered by the broker into the messages queue."""

        @tornado.gen.coroutine
        def deliver():
            """Gets all messages that are pending to be delivered into the messages queue."""

            assert broker_url in self._clients
            assert broker_url in self._deliver_stop_events

            if broker_url not in self._messages:
                self._messages[broker_url] = {}

            while not self._deliver_stop_events[broker_url].is_set():
                try:
                    msg = yield self._clients[broker_url].deliver_message(
                        timeout=self._deliver_timeout_secs)

                    if msg.topic not in self._messages[broker_url]:
                        self._messages[broker_url][msg.topic] = []

                    try:
                        self._messages[broker_url][msg.topic].append({
                            "id": uuid.uuid4().hex,
                            "data": json.loads(msg.data.decode()),
                            "time": time.time()
                        })

                        self._msg_conditions[broker_url][msg.topic].notify_all()
                    except (JSONDecodeError, TypeError, ValueError):
                        self._logr.warning("Error decoding: {}".format(msg.data), exc_info=True)
                except asyncio.TimeoutError:
                    pass
                except Exception as ex:
                    self._logr.warning("Exception delivering message: {}".format(ex), exc_info=True)
                    self._logr.debug("Sleeping for {} seconds".format(self.SLEEP_SECS_DELIVER_ERR))
                    yield tornado.gen.sleep(self.SLEEP_SECS_DELIVER_ERR)

                self._clean_messages(broker_url)

            self._deliver_stop_events[broker_url].clear()

        return deliver

    def _increase_ref(self, broker_url, ref_id):
        """Increases the reference counter for the MQTT client on the given broker URL."""

        if broker_url not in self._client_ref_counter:
            self._client_ref_counter[broker_url] = set()

        self._logr.debug("Adding ref {} to MQTT client {}".format(ref_id, broker_url))

        self._client_ref_counter[broker_url].add(ref_id)

    def _decrease_ref(self, broker_url, ref_id):
        """Decreases the reference counter for the MQTT client on the given broker URL."""

        assert broker_url in self._client_ref_counter

        try:
            self._client_ref_counter[broker_url].remove(ref_id)
            self._logr.debug("Removed ref {} from MQTT client {}".format(ref_id, broker_url))
        except KeyError:
            self._logr.warning("Removed unknown reference: {}".format(ref_id))

    @tornado.gen.coroutine
    def _init_client(self, broker_url, ref_id):
        """Initializes and connects a client to the given broker URL."""

        with (yield self._lock_client.acquire()):
            self._increase_ref(broker_url, ref_id)

            if broker_url in self._clients:
                return

            self._logr.debug("Connecting MQTT client: {}".format(broker_url))

            client = hbmqtt.client.MQTTClient()

            try:
                yield client.connect(broker_url)
            except Exception as ex:
                self._logr.warning("Error connecting: {}".format(ex), exc_info=True)
                self._decrease_ref(broker_url, ref_id)
                return

            self._clients[broker_url] = client
            self._deliver_stop_events[broker_url] = tornado.locks.Event()
            tornado.ioloop.IOLoop.current().add_callback(self._build_deliver(broker_url))

    @tornado.gen.coroutine
    def _disconnect_client(self, broker_url, ref_id):
        """Disconnects and removes references to a client for the given broker URL."""

        with (yield self._lock_client.acquire()):
            if broker_url not in self._clients:
                return

            self._decrease_ref(broker_url, ref_id)

            if len(self._client_ref_counter[broker_url]):
                return

            self._logr.debug("Disconnecting MQTT client: {}".format(broker_url))

            try:
                yield self._clients[broker_url].disconnect()
            except Exception as ex:
                self._logr.warning("Error disconnecting: {}".format(ex), exc_info=True)

            self._clients.pop(broker_url)
            self._messages.pop(broker_url, None)
            self._msg_conditions.pop(broker_url, None)

            self._deliver_stop_events[broker_url].set()

            while self._deliver_stop_events[broker_url].is_set():
                yield tornado.gen.sleep(self.DELIVER_TERMINATE_LOOP_SLEEP_SECS)

            self._deliver_stop_events.pop(broker_url)

    @tornado.gen.coroutine
    def _subscribe(self, broker_url, topic, qos):
        """Subscribes to a topic."""

        with (yield self._lock_client.acquire()):
            if broker_url not in self._clients:
                return

            if broker_url not in self._msg_conditions:
                self._msg_conditions[broker_url] = {}

            if topic not in self._msg_conditions[broker_url]:
                self._msg_conditions[broker_url][topic] = tornado.locks.Condition()

            yield self._clients[broker_url].subscribe([(topic, qos)])

    @tornado.gen.coroutine
    def _publish(self, broker_url, topic, payload, qos):
        """Publishes a message with the given payload in a topic."""

        with (yield self._lock_client.acquire()):
            if broker_url not in self._clients:
                return

            yield self._clients[broker_url].publish(topic, payload, qos=qos)

    def _topic_messages(self, broker_url, topic, from_time=None, ignore_ids=None):
        """Returns a generator that yields the messages in the
        delivered messages queue for the given topic."""

        if broker_url not in self._messages:
            return

        if topic not in self._messages[broker_url]:
            return

        for msg in self._messages[broker_url][topic]:
            is_on_time = from_time is None or msg["time"] >= from_time
            is_ignored = ignore_ids is not None and msg["id"] in ignore_ids

            if is_on_time and not is_ignored:
                yield msg["id"], msg["data"]

    def _clean_messages(self, broker_url):
        """Removes the messages that have expired according to the TTL."""

        if broker_url not in self._messages:
            return

        now = time.time()

        self._messages[broker_url] = {
            topic: [
                msg for msg in self._messages[broker_url][topic]
                if (now - msg["time"]) < self._msg_ttl_secs
            ] for topic in self._messages[broker_url]
        }

    @tornado.gen.coroutine
    def _wait_on_message(self, broker_url, topic):
        """Waits for the arrival of a message in the given topic."""

        assert broker_url in self._msg_conditions, "Unknown broker URL"
        assert topic in self._msg_conditions[broker_url], "Unknown topic"

        wait_timeout = datetime.timedelta(seconds=self._msg_wait_timeout_secs)

        yield self._msg_conditions[broker_url][topic].wait(timeout=wait_timeout)

    @classmethod
    def _pick_mqtt_href(cls, td, forms, op=None):
        """Picks the most appropriate MQTT form href from the given list of forms."""

        def is_op_form(form):
            try:
                return op is None or op == form.op or op in form.op
            except TypeError:
                return False

        return next((
            form.href for form in forms
            if is_scheme_form(form, td.base, MQTTSchemes.MQTT) and is_op_form(form)
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

        ref_id = uuid.uuid4().hex

        href = self._pick_mqtt_href(td, td.get_action_forms(name))

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)
        broker_url = parsed_href["broker_url"]

        topic_invoke = parsed_href["topic"]
        topic_result = ActionMQTTHandler.to_result_topic(topic_invoke)

        try:
            yield self._init_client(broker_url, ref_id)
            yield self._subscribe(broker_url, topic_result, self._qos)

            input_data = {
                "id": uuid.uuid4().hex,
                "input": input_value
            }

            input_payload = json.dumps(input_data).encode()

            yield self._publish(broker_url, topic_invoke, input_payload, self._qos)

            while True:
                msg_match = next((
                    item for item in self._topic_messages(broker_url, topic_result)
                    if item[1].get("id") == input_data.get("id")
                ), None)

                if msg_match is None:
                    yield self._wait_on_message(broker_url, topic_result)
                    continue

                msg_id, msg_data = msg_match

                if msg_data.get("error", None) is not None:
                    raise Exception(msg_data.get("error"))
                else:
                    raise tornado.gen.Return(msg_data.get("result"))
        finally:
            yield self._disconnect_client(broker_url, ref_id)

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        """Updates the value of a Property on a remote Thing.
        Due to the MQTT binding design this coroutine yields as soon as the write message has
        been published and will not wait for a custom write handler that yields to another coroutine
        Returns a Future."""

        ref_id = uuid.uuid4().hex

        href_write = self._pick_mqtt_href(
            td, td.get_property_forms(name),
            op=InteractionVerbs.WRITE_PROPERTY)

        if href_write is None:
            raise FormNotFoundException()

        parsed_href_write = self._parse_href(href_write)
        broker_url = parsed_href_write["broker_url"]

        topic_write = parsed_href_write["topic"]
        topic_ack = PropertyMQTTHandler.to_write_ack_topic(topic_write)

        try:
            yield self._init_client(broker_url, ref_id)
            yield self._subscribe(broker_url, topic_ack, self._qos)

            write_data = {
                "action": "write",
                "value": value,
                "ack": uuid.uuid4().hex
            }

            write_payload = json.dumps(write_data).encode()

            yield self._publish(broker_url, topic_write, write_payload, self._qos)

            if not self._wait_on_write:
                return

            while True:
                msg_match = next((
                    item for item in self._topic_messages(broker_url, topic_ack)
                    if item[1].get("ack") == write_data.get("ack")
                ), None)

                if msg_match is not None:
                    break

                yield self._wait_on_message(broker_url, topic_ack)
        finally:
            yield self._disconnect_client(broker_url, ref_id)

    @tornado.gen.coroutine
    def read_property(self, td, name):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        ref_id = uuid.uuid4().hex

        forms = td.get_property_forms(name)

        href_read = self._pick_mqtt_href(td, forms, op=InteractionVerbs.READ_PROPERTY)
        href_obsv = self._pick_mqtt_href(td, forms, op=InteractionVerbs.OBSERVE_PROPERTY)

        if href_read is None or href_obsv is None:
            raise FormNotFoundException()

        parsed_href_read = self._parse_href(href_read)
        parsed_href_obsv = self._parse_href(href_obsv)

        topic_read = parsed_href_read["topic"]
        topic_obsv = parsed_href_obsv["topic"]

        broker_read = parsed_href_read["broker_url"]
        broker_obsv = parsed_href_obsv["broker_url"]

        try:
            yield self._init_client(broker_read, ref_id)
            broker_obsv != broker_read and (yield self._init_client(broker_obsv, ref_id))

            yield self._subscribe(broker_obsv, topic_obsv, self._qos)

            read_time = int(time.time() * 1000)
            read_payload = json.dumps({"action": "read"}).encode()

            yield self._publish(broker_read, topic_read, read_payload, self._qos)

            while True:
                msg_match = next((
                    item for item in self._topic_messages(broker_obsv, topic_obsv)
                    if item[1].get("timestamp") >= read_time
                ), None)

                if msg_match is None:
                    yield self._wait_on_message(broker_obsv, topic_obsv)
                    continue

                msg_id, msg_data = msg_match

                raise tornado.gen.Return(msg_data.get("value"))
        finally:
            yield self._disconnect_client(broker_read, ref_id)
            broker_obsv != broker_read and (yield self._disconnect_client(broker_obsv, ref_id))

    def _build_subscribe(self, broker_url, topic, next_item_builder):
        """Builds the subscribe function that should be passed when
        constructing an Observable to listen for messages on an MQTT topic."""

        def subscribe(observer):
            """Subscriber function that listens for MQTT messages
            on a given topic and passes them to the Observer."""

            ref_id = uuid.uuid4().hex

            state = {"active": True}

            @handle_observer_finalization(observer)
            @tornado.gen.coroutine
            def callback():
                from_time = time.time()
                emitted_ids = set()

                yield self._init_client(broker_url, ref_id)
                yield self._subscribe(broker_url, topic, self._qos)

                while state["active"]:
                    msgs_to_emit_gen = self._topic_messages(
                        broker_url, topic,
                        from_time=from_time,
                        ignore_ids=emitted_ids)

                    for msg_id, msg_data in msgs_to_emit_gen:
                        next_item = next_item_builder(msg_data)
                        observer.on_next(next_item)
                        emitted_ids.add(msg_id)

                    yield self._wait_on_message(broker_url, topic)

            def unsubscribe():
                """Disconnects from the MQTT broker and stops the message delivering loop."""

                state["active"] = False

                @tornado.gen.coroutine
                def disconnect():
                    yield self._disconnect_client(broker_url, ref_id)

                tornado.ioloop.IOLoop.current().add_callback(disconnect)

            tornado.ioloop.IOLoop.current().add_callback(callback)

            return unsubscribe

        return subscribe

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        forms = td.get_property_forms(name)
        href = self._pick_mqtt_href(td, forms, op=InteractionVerbs.OBSERVE_PROPERTY)

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)

        broker_url = parsed_href["broker_url"]
        topic = parsed_href["topic"]

        def next_item_builder(msg_data):
            msg_value = msg_data.get("value")
            init = PropertyChangeEventInit(name=name, value=msg_value)
            return PropertyChangeEmittedEvent(init=init)

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
        href = self._pick_mqtt_href(td, forms, op=InteractionVerbs.SUBSCRIBE_EVENT)

        if href is None:
            raise FormNotFoundException()

        parsed_href = self._parse_href(href)

        broker_url = parsed_href["broker_url"]
        topic = parsed_href["topic"]

        def next_item_builder(msg_data):
            return EmittedEvent(init=msg_data.get("data"), name=name)

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
