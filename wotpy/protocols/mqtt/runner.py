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

    def __init__(self, broker_url, mqtt_handler, timeout_deliver_secs=DEFAULT_TIMEOUT_DELIVER_SECS):
        self._broker_url = broker_url
        self._mqtt_handler = mqtt_handler
        self._timeout_deliver_secs = timeout_deliver_secs
        self._client = None
        self._lock_conn = tornado.locks.Lock()
        self._lock_run = tornado.locks.Lock()
        self._event_stop_request = tornado.locks.Event()

    @tornado.gen.coroutine
    def connect(self):
        """Connects to the MQTT broker.
        Disconnects first if necessary."""

        with (yield self._lock_conn.acquire()):
            yield self._disconnect()

            hbmqtt_client = MQTTClient()

            ack_con = yield hbmqtt_client.connect(self._broker_url)

            if ack_con != MQTTCodesACK.CON_OK:
                raise ConnectException("Error code in connection ACK: {}".format(ack_con))

            ack_sub = yield hbmqtt_client.subscribe(self._mqtt_handler.topics)

            if MQTTCodesACK.SUB_ERROR in ack_sub:
                raise ConnectException("Error code in subscription ACK: {}".format(ack_sub))

            self._client = hbmqtt_client

    @tornado.gen.coroutine
    def _disconnect(self):
        """Helper function to disconnect from the MQTT broker."""

        if self._client is None:
            return

        client = self._client
        self._client = None

        yield client.unsubscribe([name for name, qos in self._mqtt_handler.topics])
        yield client.disconnect()

    @tornado.gen.coroutine
    def disconnect(self):
        """Disconnects from the MQTT broker."""

        with (yield self._lock_conn.acquire()):
            yield self._disconnect()

    @tornado.gen.coroutine
    def handle_delivered_message(self):
        """Listens and processes the next published message.
        It will wait for a finite amount of time before desisting."""

        try:
            msg = yield self._client.deliver_message(timeout=self._timeout_deliver_secs)
            yield self._mqtt_handler.handle_message(msg)
        except asyncio.TimeoutError:
            pass

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
            logging.warning("MQTT handler error ({}): {}".format(self._mqtt_handler.__class__, ex))

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
                logging.warning("Attempted to start an MQTT handler loop when another was already running")

        tornado.ioloop.IOLoop.current().spawn_callback(run_loop)

    @tornado.gen.coroutine
    def start(self):
        """Starts listening for published messages."""

        self._event_stop_request.set()

        with (yield self._lock_run.acquire()):
            self._event_stop_request.clear()

        yield self._mqtt_handler.init()

        self._add_loop_callback()

    @tornado.gen.coroutine
    def stop(self):
        """Stops listening for published messages."""

        self._event_stop_request.set()

        with (yield self._lock_run.acquire()):
            pass

        yield self._mqtt_handler.teardown()
