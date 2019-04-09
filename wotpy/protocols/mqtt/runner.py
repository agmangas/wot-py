#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class for MQTT handlers.
"""

import asyncio
import copy
import datetime
import logging
import uuid

import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.locks
import tornado.util
from hbmqtt.client import MQTTClient, ConnectException
from tornado.queues import Queue

from wotpy.protocols.mqtt.enums import MQTTCodesACK


class MQTTHandlerRunner(object):
    """Class that wraps an MQTT handler. It handles connections to the
    MQTT broker, delivers messages, and runs the handler in a loop."""

    DEFAULT_TIMEOUT_LOOPS_SECS = 0.1
    DEFAULT_SLEEP_ERR_RECONN = 2.0
    DEFAULT_MSGS_BUF_SIZE = 500

    # Highly permissive default keep_alive to avoid
    # disconnections from broker on high throughput scenarios:
    # https://github.com/beerfactory/hbmqtt/issues/119#issuecomment-430398094

    DEFAULT_CLIENT_CONFIG = {
        "keep_alive": 90
    }

    def __init__(self, broker_url, mqtt_handler,
                 messages_buffer_size=DEFAULT_MSGS_BUF_SIZE,
                 timeout_loops=DEFAULT_TIMEOUT_LOOPS_SECS,
                 sleep_error_reconnect=DEFAULT_SLEEP_ERR_RECONN,
                 hbmqtt_config=None):
        self._broker_url = broker_url
        self._mqtt_handler = mqtt_handler
        self._messages_buffer = Queue(maxsize=messages_buffer_size)
        self._timeout_loops_secs = timeout_loops
        self._sleep_error_reconnect = sleep_error_reconnect
        self._hbmqtt_config = hbmqtt_config
        self._client = None
        self._client_id = uuid.uuid4().hex
        self._lock_conn = tornado.locks.Lock()
        self._lock_run = tornado.locks.Lock()
        self._event_stop_request = tornado.locks.Event()
        self._logr = logging.getLogger(__name__)

    def _log(self, level, msg, **kwargs):
        """Helper function to wrap all log messages."""

        self._logr.log(level, "{} - {}".format(self._mqtt_handler.__class__.__name__, msg), **kwargs)

    def _build_client_config(self):
        """Returns the config dict for a new hbmqtt client instance."""

        config = copy.copy(self.DEFAULT_CLIENT_CONFIG)
        config_arg = self._hbmqtt_config if self._hbmqtt_config else {}
        config.update(config_arg)

        # The library does not resubscribe when reconnecting.
        # We need to handle it manually.

        config.update({"auto_reconnect": False})

        return config

    @tornado.gen.coroutine
    def _connect(self):
        """MQTT connection helper function."""

        config = self._build_client_config()

        self._log(logging.DEBUG, "MQTT client ID: {}".format(self._client_id))
        self._log(logging.DEBUG, "MQTT client config: {}".format(config))

        hbmqtt_client = MQTTClient(client_id=self._client_id, config=config)

        self._log(logging.INFO, "Connecting MQTT client to broker: {}".format(self._broker_url))

        ack_con = yield hbmqtt_client.connect(self._broker_url, cleansession=False)

        if ack_con != MQTTCodesACK.CON_OK:
            raise ConnectException("Error code in connection ACK: {}".format(ack_con))

        if self._mqtt_handler.topics:
            self._log(logging.DEBUG, "Subscribing to: {}".format(self._mqtt_handler.topics))
            ack_sub = yield hbmqtt_client.subscribe(self._mqtt_handler.topics)

            if MQTTCodesACK.SUB_ERROR in ack_sub:
                raise ConnectException("Error code in subscription ACK: {}".format(ack_sub))

        self._client = hbmqtt_client

    @tornado.gen.coroutine
    def _disconnect(self):
        """MQTT disconnection helper function."""

        try:
            self._log(logging.DEBUG, "Disconnecting MQTT client")

            if self._mqtt_handler.topics:
                self._log(logging.DEBUG, "Unsubscribing from: {}".format(self._mqtt_handler.topics))
                yield self._client.unsubscribe([name for name, qos in self._mqtt_handler.topics])

            yield self._client.disconnect()
        except Exception as ex:
            self._log(logging.DEBUG, "Error disconnecting MQTT client: {}".format(ex), exc_info=True)
        finally:
            self._client = None

    @tornado.gen.coroutine
    def connect(self, force_reconnect=False):
        """Connects to the MQTT broker."""

        with (yield self._lock_conn.acquire()):
            if self._client is not None and force_reconnect:
                self._log(logging.DEBUG, "Forcing reconnection")
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
    def _deliver_messages(self):
        """Receives messages from the MQTT broker and puts them in the internal buffer."""

        message = None

        while not self._event_stop_request.is_set():
            if message is None:
                try:
                    message = yield self._client.deliver_message(timeout=self._timeout_loops_secs)
                except asyncio.TimeoutError:
                    pass
                except Exception as ex:
                    self._log(logging.WARNING, "Error on MQTT deliver: {}".format(ex))

                    try:
                        yield tornado.gen.sleep(self._sleep_error_reconnect)
                        yield self.connect(force_reconnect=True)
                    except Exception as ex:
                        self._log(logging.ERROR, "Error reconnecting: {}".format(ex), exc_info=True)

            if message is not None:
                try:
                    timeout_put = datetime.timedelta(seconds=self._timeout_loops_secs)
                    yield self._messages_buffer.put(message, timeout=timeout_put)
                    message = None
                except tornado.util.TimeoutError:
                    self._log(logging.DEBUG, "Full messages buffer")

    @tornado.gen.coroutine
    def _handle_messages(self):
        """Gets messages from the internal buffer and
        passes them to the MQTT handler to be processed."""

        while not self._event_stop_request.is_set():
            try:
                timeout_get = datetime.timedelta(seconds=self._timeout_loops_secs)
                message = yield self._messages_buffer.get(timeout=timeout_get)
                self._log(logging.DEBUG, "Handling message: {}".format(message.data))
                tornado.gen.convert_yielded(self._mqtt_handler.handle_message(message))
            except tornado.util.TimeoutError:
                pass
            except Exception as ex:
                self._log(logging.WARNING, "MQTT handler error: {}".format(ex), exc_info=True)

    @tornado.gen.coroutine
    def _publish_queued_messages(self):
        """Gets the pending messages from the handler queue and publishes them on the broker."""

        message = None

        while not self._event_stop_request.is_set():
            try:
                if message is None:
                    timeout_get = datetime.timedelta(seconds=self._timeout_loops_secs)
                    message = yield self._mqtt_handler.queue.get(timeout=timeout_get)
                else:
                    self._log(logging.WARNING, "Republish attempt: {}".format(message))

                yield self._client.publish(
                    topic=message["topic"],
                    message=message["data"],
                    qos=message.get("qos", None),
                    retain=message.get("retain", None))

                message = None
            except tornado.util.TimeoutError:
                pass
            except Exception as ex:
                self._log(logging.WARNING, "Exception publishing: {}".format(ex), exc_info=True)
                yield tornado.gen.sleep(self._sleep_error_reconnect)

    def _add_loop_callback(self):
        """Adds the callback that will start the infinite loop
        to listen and handle the messages published in the topics
        that are of interest to this MQTT client."""

        @tornado.gen.coroutine
        def run_loop():
            try:
                with (yield self._lock_run.acquire(timeout=0)):
                    self._log(logging.DEBUG, "Entering MQTT runner loop")

                    yield [
                        self._deliver_messages(),
                        self._handle_messages(),
                        self._publish_queued_messages()
                    ]
            except tornado.util.TimeoutError:
                self._log(logging.WARNING, "Cannot start MQTT handler loop while another is already running")

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
