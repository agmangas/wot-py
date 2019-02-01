#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the MQTT protocol.
"""

import asyncio
import datetime
import json
import logging
import pprint
import time
import uuid

import hbmqtt.client
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.locks
from hbmqtt.mqtt.constants import QOS_2, QOS_1, QOS_0
from rx import Observable
from six.moves.urllib import parse

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.enums import Protocols, InteractionVerbs
from wotpy.protocols.exceptions import FormNotFoundException
from wotpy.protocols.mqtt.enums import MQTTSchemes
from wotpy.protocols.mqtt.handlers.action import ActionMQTTHandler
from wotpy.protocols.mqtt.handlers.property import PropertyMQTTHandler
from wotpy.protocols.refs import ConnRefCounter
from wotpy.protocols.utils import is_scheme_form
from wotpy.utils.utils import handle_observer_finalization
from wotpy.wot.events import PropertyChangeEventInit, PropertyChangeEmittedEvent, EmittedEvent


class MQTTClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the MQTT protocol."""

    DELIVER_TERMINATE_LOOP_SLEEP_SECS = 0.1
    SLEEP_SECS_DELIVER_ERR = 1.0

    def __init__(self, deliver_timeout_secs=1, msg_wait_timeout_secs=5, msg_ttl_secs=15,
                 timeout_default=None, config=None, deliver_loop_timeout_secs=20):
        self._deliver_timeout_secs = deliver_timeout_secs
        self._msg_wait_timeout_secs = msg_wait_timeout_secs
        self._msg_ttl_secs = msg_ttl_secs
        self._timeout_default = timeout_default
        self._config = config
        self._deliver_loop_timeout_secs = deliver_loop_timeout_secs
        self._lock_client = tornado.locks.Lock()
        self._deliver_stop_events = {}
        self._msg_conditions = {}
        self._clients = {}
        self._messages = {}
        self._topics = {}
        self._ref_counter = ConnRefCounter()
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

            while broker_url in self._deliver_stop_events and not self._deliver_stop_events[broker_url].is_set():
                try:
                    msg = yield self._clients[broker_url].deliver_message(timeout=self._deliver_timeout_secs)
                except asyncio.TimeoutError:
                    continue
                except Exception as ex:
                    self._logr.warning("Error delivering message: {}".format(ex), exc_info=True)

                    try:
                        self._logr.debug("Sleeping for {} seconds".format(self.SLEEP_SECS_DELIVER_ERR))
                        yield tornado.gen.sleep(self.SLEEP_SECS_DELIVER_ERR)
                        yield self._reconnect_client(broker_url)
                    except Exception as ex_reconn:
                        self._logr.warning("Error reconnecting: {}".format(ex_reconn), exc_info=True)

                    continue

                try:
                    if msg.topic not in self._messages[broker_url]:
                        self._messages[broker_url][msg.topic] = []

                    self._messages[broker_url][msg.topic].append({
                        "id": uuid.uuid4().hex,
                        "data": json.loads(msg.data.decode()),
                        "time": time.time()
                    })

                    self._msg_conditions[broker_url][msg.topic].notify_all()
                    self._clean_messages(broker_url)
                except Exception as ex:
                    self._logr.warning("Error processing message: {}".format(ex), exc_info=True)

            broker_url in self._deliver_stop_events and self._deliver_stop_events[broker_url].clear()

        return deliver

    @tornado.gen.coroutine
    def _init_client(self, broker_url, ref_id):
        """Initializes and connects a client to the given broker URL."""

        with (yield self._lock_client.acquire()):
            self._ref_counter.increase(broker_url, ref_id)

            if broker_url in self._clients:
                return

            config = self._config if self._config else {}
            config.update({"auto_reconnect": False})

            self._logr.debug("Connecting MQTT client to {} with config: {}".format(
                broker_url, pprint.pformat(config)))

            self._clients[broker_url] = hbmqtt.client.MQTTClient(config=config)

            yield self._clients[broker_url].connect(broker_url, cleansession=False)

            self._deliver_stop_events[broker_url] = tornado.locks.Event()
            tornado.ioloop.IOLoop.current().add_callback(self._build_deliver(broker_url))

    @tornado.gen.coroutine
    def _disconnect_client(self, broker_url, ref_id):
        """Decreases the reference counter for the client on the given broker and cleans
        all resources when the client does not have any more references pointing to it."""

        with (yield self._lock_client.acquire()):
            self._ref_counter.decrease(broker_url, ref_id)

            if self._ref_counter.has_any(broker_url):
                return

            if broker_url in self._deliver_stop_events:
                self._logr.debug("Stopping message delivery loop: {}".format(broker_url))

                self._deliver_stop_events[broker_url].set()

                now = time.time()

                def has_time_left():
                    return (time.time() - now) < self._deliver_loop_timeout_secs

                while self._deliver_stop_events[broker_url].is_set() and has_time_left():
                    yield tornado.gen.sleep(self.DELIVER_TERMINATE_LOOP_SLEEP_SECS)

                self._deliver_stop_events.pop(broker_url)

            try:
                if broker_url in self._clients:
                    self._logr.debug("Disconnecting MQTT client: {}".format(broker_url))
                    yield self._clients[broker_url].disconnect()
            except Exception as ex:
                self._logr.warning("Error disconnecting: {}".format(ex), exc_info=True)

            self._clients.pop(broker_url, None)
            self._messages.pop(broker_url, None)
            self._msg_conditions.pop(broker_url, None)
            self._topics.pop(broker_url, None)

    @tornado.gen.coroutine
    def _reconnect_client(self, broker_url):
        """Reconnects an existing client that has been disconnected."""

        with (yield self._lock_client.acquire()):
            if broker_url not in self._clients:
                self._logr.warning("Attempted to reconnect unknown client: {}".format(broker_url))
                return

            self._logr.info("Reconnecting MQTT client: {}".format(broker_url))

            yield self._clients[broker_url].reconnect(cleansession=False)

            topics = self._topics.get(broker_url, set())

            if not len(topics):
                return

            self._logr.info("Resubscribing MQTT client on {} to topics:\n{}".format(
                broker_url, pprint.pformat(topics)))

            yield self._clients[broker_url].subscribe([(topic, qos) for topic, qos in topics])

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

            if broker_url not in self._topics:
                self._topics[broker_url] = set()

            self._topics[broker_url].add((topic, qos))

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

    def _next_match(self, broker_url, topic, func):
        """Returns the first message match in the internal messages queue or None."""

        return next((item for item in self._topic_messages(broker_url, topic) if func(item)), None)

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
    def invoke_action(self, td, name, input_value,
                      timeout=None, qos_publish=QOS_2, qos_subscribe=QOS_1):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        timeout = timeout if timeout else self._timeout_default
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
            yield self._subscribe(broker_url, topic_result, qos_subscribe)

            input_data = {
                "id": uuid.uuid4().hex,
                "input": input_value
            }

            input_payload = json.dumps(input_data).encode()

            yield self._publish(broker_url, topic_invoke, input_payload, qos_publish)

            ini = time.time()

            while True:
                self._logr.debug("Checking invocation topic: {}".format(topic_result))

                if timeout and (time.time() - ini) > timeout:
                    self._logr.warning("Timeout invoking Action: {}".format(topic_result))
                    raise asyncio.TimeoutError("Exceeded timeout ({} secs)".format(timeout))

                msg_match = self._next_match(
                    broker_url, topic_result,
                    lambda item: item[1].get("id") == input_data.get("id"))

                if not msg_match:
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
    def write_property(self, td, name, value,
                       timeout=None, qos_publish=QOS_1, qos_subscribe=QOS_1, wait_ack=True):
        """Updates the value of a Property on a remote Thing.
        Due to the MQTT binding design this coroutine yields as soon as the write message has
        been published and will not wait for a custom write handler that yields to another coroutine
        Returns a Future."""

        timeout = timeout if timeout else self._timeout_default
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
            yield self._subscribe(broker_url, topic_ack, qos_subscribe)

            write_data = {
                "action": "write",
                "value": value,
                "ack": uuid.uuid4().hex
            }

            write_payload = json.dumps(write_data).encode()

            yield self._publish(broker_url, topic_write, write_payload, qos_publish)

            if not wait_ack:
                return

            ini = time.time()

            while True:
                self._logr.debug("Checking write ACK topic: {}".format(topic_ack))

                if timeout and (time.time() - ini) > timeout:
                    self._logr.warning("Timeout writing Property: {}".format(topic_ack))
                    raise asyncio.TimeoutError("Exceeded timeout ({} secs)".format(timeout))

                msg_match = self._next_match(
                    broker_url, topic_ack,
                    lambda item: item[1].get("ack") == write_data.get("ack"))

                if msg_match:
                    break

                yield self._wait_on_message(broker_url, topic_ack)
        finally:
            yield self._disconnect_client(broker_url, ref_id)

    @tornado.gen.coroutine
    def read_property(self, td, name,
                      timeout=None, qos_publish=QOS_1, qos_subscribe=QOS_1):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        timeout = timeout if timeout else self._timeout_default
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

            yield self._subscribe(broker_obsv, topic_obsv, qos_subscribe)

            read_time = int(time.time() * 1000)
            read_payload = json.dumps({"action": "read"}).encode()

            yield self._publish(broker_read, topic_read, read_payload, qos_publish)

            ini = time.time()

            while True:
                self._logr.debug("Checking property update topic: {}".format(topic_obsv))

                if timeout and (time.time() - ini) > timeout:
                    self._logr.warning("Timeout reading Property: {}".format(topic_obsv))
                    raise asyncio.TimeoutError("Exceeded timeout ({} secs)".format(timeout))

                msg_match = self._next_match(
                    broker_obsv, topic_obsv,
                    lambda item: item[1].get("timestamp") >= read_time)

                if not msg_match:
                    yield self._wait_on_message(broker_obsv, topic_obsv)
                    continue

                msg_id, msg_data = msg_match

                raise tornado.gen.Return(msg_data.get("value"))
        finally:
            yield self._disconnect_client(broker_read, ref_id)
            broker_obsv != broker_read and (yield self._disconnect_client(broker_obsv, ref_id))

    def _build_subscribe(self, broker_url, topic, next_item_builder, qos):
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
                yield self._subscribe(broker_url, topic, qos)

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

    def on_property_change(self, td, name, qos=QOS_0):
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
            next_item_builder=next_item_builder,
            qos=qos)

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_event(self, td, name, qos=QOS_0):
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
            next_item_builder=next_item_builder,
            qos=qos)

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
