#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class for MQTT handlers.
"""

# noinspection PyCompatibility
import asyncio
import logging

import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.locks
import tornado.util
from hbmqtt.client import MQTTClient, ConnectException
from tornado.queues import QueueEmpty

from wotpy.protocols.mqtt.enums import MQTTCodesACK


class MQTTHandlerRunner(object):
    """Class that wraps an MQTT handler. It handles connections to the
    MQTT broker, delivers messages, and runs the handler in a loop."""

    DEFAULT_TIMEOUT_DELIVER_SECS = 0.1
    DEFAULT_MESSAGES_BATCH_SIZE = 50

    DEFAULT_CLIENT_CONFIG = {
        "keep_alive": 10,
        "auto_reconnect": True,
        "default_qos": 0,
        "default_retain": False
    }

    def __init__(self, broker_url, mqtt_handler,
                 timeout_deliver_secs=DEFAULT_TIMEOUT_DELIVER_SECS,
                 messages_batch_size=DEFAULT_MESSAGES_BATCH_SIZE,
                 reconnect_on_handler_error=True,
                 client_config=None):
        self._broker_url = broker_url
        self._mqtt_handler = mqtt_handler
        self._timeout_deliver_secs = timeout_deliver_secs
        self._messages_batch_size = messages_batch_size
        self._reconnect_on_handler_error = reconnect_on_handler_error
        self._client_config = client_config if client_config else self.DEFAULT_CLIENT_CONFIG
        self._client = None
        self._lock_conn = tornado.locks.Lock()
        self._lock_run = tornado.locks.Lock()
        self._event_stop_request = tornado.locks.Event()
        self._logr = logging.getLogger(__name__)

    @tornado.gen.coroutine
    def _connect(self):
        """MQTT connection helper function."""

        self._logr.debug("Using MQTT client config: {}".format(self._client_config))

        hbmqtt_client = MQTTClient(config=self._client_config)

        self._logr.debug("Connecting MQTT client to broker: {}".format(self._broker_url))

        ack_con = yield hbmqtt_client.connect(self._broker_url)

        if ack_con != MQTTCodesACK.CON_OK:
            raise ConnectException("Error code in connection ACK: {}".format(ack_con))

        if self._mqtt_handler.topics:
            self._logr.debug("Subscribing to: {}".format(self._mqtt_handler.topics))
            ack_sub = yield hbmqtt_client.subscribe(self._mqtt_handler.topics)

            if MQTTCodesACK.SUB_ERROR in ack_sub:
                raise ConnectException("Error code in subscription ACK: {}".format(ack_sub))

        self._client = hbmqtt_client

    @tornado.gen.coroutine
    def _disconnect(self):
        """MQTT disconnection helper function."""

        try:
            self._logr.debug("Disconnecting MQTT client")

            if self._mqtt_handler.topics:
                self._logr.debug("Unsubscribing from: {}".format(self._mqtt_handler.topics))
                yield self._client.unsubscribe([name for name, qos in self._mqtt_handler.topics])

            yield self._client.disconnect()
        except Exception as ex:
            self._logr.warning("Error disconnecting MQTT client: {}".format(ex), exc_info=True)
        finally:
            self._client = None

    @tornado.gen.coroutine
    def connect(self, force_reconnect=False):
        """Connects to the MQTT broker."""

        with (yield self._lock_conn.acquire()):
            if self._client is not None and force_reconnect:
                yield self._disconnect()
            elif self._client is not None:
                return

            yield self._connect()

    @tornado.gen.coroutine
    def disconnect(self):
        """Disconnects from the MQTT broker."""

        with (yield self._lock_conn.acquire()):
            if self._client is None:
                return

            yield self._disconnect()

    @tornado.gen.coroutine
    def handle_delivered_message(self):
        """Listens and processes the next published message.
        It will wait for a finite amount of time before desisting."""

        msgs = []

        try:
            while len(msgs) < self._messages_batch_size:
                msg = yield self._client.deliver_message(timeout=self._timeout_deliver_secs)
                msgs.append(msg)
        except asyncio.TimeoutError:
            pass

        if not len(msgs):
            return

        yield [self._mqtt_handler.handle_message(msg) for msg in msgs]

    @tornado.gen.coroutine
    def publish_queued_messages(self):
        """Gets the pending messages from the handler queue and publishes them on the broker."""

        messages = []

        try:
            while self._mqtt_handler.queue.qsize() > 0:
                messages.append(self._mqtt_handler.queue.get_nowait())
        except QueueEmpty:
            pass

        def publish_msg(msg):
            return self._client.publish(
                topic=msg["topic"], message=msg["data"],
                qos=msg.get("qos", None), retain=msg.get("retain", None))

        yield [publish_msg(msg) for msg in messages]

    @tornado.gen.coroutine
    def handler_loop_iter(self):
        """Process an iteration of the MQTT handler loop."""

        try:
            yield self.handle_delivered_message()
            yield self.publish_queued_messages()
        except Exception as ex:
            self._logr.warning(
                "MQTT handler error ({}): {}".format(self._mqtt_handler.__class__, ex),
                exc_info=True)

            if self._reconnect_on_handler_error:
                self._logr.warning("Attempting to reconnect MQTT client")
                yield self.connect(force_reconnect=True)

    def _add_loop_callback(self):
        """Adds the callback that will start the infinite loop
        to listen and handle the messages published in the topics
        that are of interest to this MQTT client."""

        @tornado.gen.coroutine
        def run_loop():
            try:
                with (yield self._lock_run.acquire(timeout=0)):
                    while not self._event_stop_request.is_set():
                        yield self.handler_loop_iter()
            except tornado.util.TimeoutError:
                self._logr.warning("Attempted to start an MQTT handler loop when another was already running")

        tornado.ioloop.IOLoop.current().spawn_callback(run_loop)

    @tornado.gen.coroutine
    def start(self):
        """Starts listening for published messages."""

        self._event_stop_request.set()

        with (yield self._lock_run.acquire()):
            self._event_stop_request.clear()

        yield self.connect(force_reconnect=True)

        yield self._mqtt_handler.init()

        self._add_loop_callback()

    @tornado.gen.coroutine
    def stop(self):
        """Stops listening for published messages."""

        self._event_stop_request.set()

        with (yield self._lock_run.acquire()):
            pass

        yield self._mqtt_handler.teardown()

        yield self.disconnect()
