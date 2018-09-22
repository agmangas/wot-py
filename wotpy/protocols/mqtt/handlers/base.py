#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class for MQTT handlers.
"""

import logging
# noinspection PyCompatibility
from asyncio import TimeoutError

import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.locks
import tornado.util
from hbmqtt.client import MQTTClient, ConnectException

from wotpy.protocols.mqtt.enums import MQTTWoTTopics


class BaseMQTTHandler(object):
    """Base class for all MQTT handlers.
    An MQTT handler is a MQTT client that subscribes to WoT request messages.
    It may publish responses to those requests."""

    DEFAULT_TIMEOUT_DELIVER_SECS = 1.0
    ACK_OK_CON = 0
    ACK_ERROR_SUB = 128

    def __init__(self, broker_url, handle_message, topics,
                 timeout_deliver_secs=DEFAULT_TIMEOUT_DELIVER_SECS):
        self._broker_url = broker_url
        self._handle_message = handle_message
        self._topics = topics
        self._client = None
        self._timeout_deliver_secs = timeout_deliver_secs
        self._run_event = tornado.locks.Event()
        self._conn_lock = tornado.locks.Lock()
        self._add_loop_callback()

    def _add_loop_callback(self):
        """Adds the callback that will start the infinite loop
        to listen and handle the messages published in the topics
        that are of interest to this MQTT client."""

        @tornado.gen.coroutine
        def run_loop():
            while True:
                yield self._run_event.wait()
                try:
                    yield self.handle_next()
                except Exception as ex:
                    logging.warning("Error in MQTT handler {}: {}".format(self.__class__, ex))

        tornado.ioloop.IOLoop.current().spawn_callback(run_loop)

    @tornado.gen.coroutine
    def connect(self):
        """Connects to the MQTT broker.
        Disconnects first if necessary."""

        with (yield self._conn_lock.acquire()):
            yield self._disconnect()

            hbmqtt_client = MQTTClient()

            ack_con = yield hbmqtt_client.connect(self._broker_url)

            if ack_con != self.ACK_OK_CON:
                raise ConnectException("Error code in connection ACK: {}".format(ack_con))

            ack_sub = yield hbmqtt_client.subscribe(self._topics)

            if self.ACK_ERROR_SUB in ack_sub:
                raise ConnectException("Error code in subscription ACK: {}".format(ack_sub))

            self._client = hbmqtt_client

    @tornado.gen.coroutine
    def _disconnect(self):
        """Helper function to disconnect from the MQTT broker."""

        if self._client is None:
            return

        client = self._client
        self._client = None

        yield client.unsubscribe([MQTTWoTTopics.PING])
        yield client.disconnect()

    @tornado.gen.coroutine
    def disconnect(self):
        """Disconnects from the MQTT broker."""

        with (yield self._conn_lock.acquire()):
            yield self._disconnect()

    @tornado.gen.coroutine
    def handle_next(self):
        """Listens and processes the next published message.
        It will wait for a finite amount of time before desisting."""

        try:
            msg = yield self._client.deliver_message(timeout=self._timeout_deliver_secs)
            yield self._handle_message(self._client, msg)
        except TimeoutError:
            pass

    def start(self):
        """Starts listening for published messages."""

        self._run_event.set()

    def stop(self):
        """Stops listening for published messages."""

        self._run_event.clear()
