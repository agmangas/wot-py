#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Base class for MQTT handlers.
"""

import asyncio
import copy
import logging
import uuid
from urllib.parse import urlparse, urlunparse

from amqtt.client import MQTTClient
try:
    from amqtt.client import ConnectError
except ImportError:
    from amqtt.client import ClientException as ConnectError

from wotpy.protocols.mqtt.enums import MQTTCodesACK


class MQTTHandlerRunner:
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

    def __init__(
        self,
        broker_url,
        mqtt_handler,
        messages_buffer_size=DEFAULT_MSGS_BUF_SIZE,
        timeout_loops=DEFAULT_TIMEOUT_LOOPS_SECS,
        sleep_error_reconnect=DEFAULT_SLEEP_ERR_RECONN,
        ca_file=None,
        amqtt_config=None,
        username=None,
        password=None
    ):
        self._mqtt_handler = mqtt_handler
        self._messages_buffer = asyncio.Queue(maxsize=messages_buffer_size)
        self._timeout_loops_secs = timeout_loops
        self._sleep_error_reconnect = sleep_error_reconnect
        self._ca_file = ca_file
        self._amqtt_config = amqtt_config
        self._username = username
        self._password = password
        if username is not None and password is not None:
            url_parts = list(urlparse(broker_url))
            url_parts[1] = f"{self._username}:{self._password}@{url_parts[1]}"
            self._broker_url = urlunparse(url_parts)
        else:
            self._broker_url = broker_url
        self._client = None
        self._client_id = uuid.uuid4().hex
        self._lock_conn = asyncio.Lock()
        self._lock_run = asyncio.Lock()
        self._event_stop_request = asyncio.Event()
        self._logr = logging.getLogger(__name__)

    def _log(self, level, msg, **kwargs):
        """Helper function to wrap all log messages."""

        self._logr.log(
            level,
            "{} - {}".format(self._mqtt_handler.__class__.__name__, msg),
            **kwargs
        )

    def _build_client_config(self):
        """Returns the config dict for a new amqtt client instance."""

        config = copy.copy(self.DEFAULT_CLIENT_CONFIG)
        config_arg = self._amqtt_config if self._amqtt_config else {}
        config.update(config_arg)

        # The library does not resubscribe when reconnecting.
        # We need to handle it manually.

        config.update({"auto_reconnect": False})

        return config

    async def _connect(self):
        """MQTT connection helper function."""

        config = self._build_client_config()

        self._log(logging.DEBUG, "MQTT client ID: {}".format(self._client_id))
        self._log(logging.DEBUG, "MQTT client config: {}".format(config))

        amqtt_client = MQTTClient(client_id=self._client_id, config=config)

        self._log(logging.INFO, "Connecting MQTT client to broker: {}".format(self._broker_url))

        ack_con = await amqtt_client.connect(self._broker_url, cafile=self._ca_file, cleansession=False)

        if ack_con != MQTTCodesACK.CON_OK:
            raise ConnectError("Error code in connection ACK: {}".format(ack_con))

        if self._mqtt_handler.topics:
            self._log(logging.DEBUG, "Subscribing to: {}".format(self._mqtt_handler.topics))
            ack_sub = await amqtt_client.subscribe(self._mqtt_handler.topics)

            if MQTTCodesACK.SUB_ERROR in ack_sub:
                raise ConnectError("Error code in subscription ACK: {}".format(ack_sub))

        self._client = amqtt_client

    async def _disconnect(self):
        """MQTT disconnection helper function."""

        try:
            self._log(logging.DEBUG, "Disconnecting MQTT client")

            if self._mqtt_handler.topics:
                self._log(logging.DEBUG, "Unsubscribing from: {}".format(self._mqtt_handler.topics))
                await self._client.unsubscribe([name for name, qos in self._mqtt_handler.topics])

            await self._client.disconnect()
        except Exception as ex:
            self._log(logging.DEBUG, "Error disconnecting MQTT client: {}".format(ex), exc_info=True)
        finally:
            self._client = None

    async def connect(self, force_reconnect=False):
        """Connects to the MQTT broker."""

        async with self._lock_conn:
            if self._client is not None and force_reconnect:
                self._log(logging.DEBUG, "Forcing reconnection")
                await self._disconnect()
            elif self._client is not None:
                return

            await self._connect()

    async def disconnect(self):
        """Disconnects from the MQTT broker."""

        async with self._lock_conn:
            if self._client is None:
                return

            await self._disconnect()

    async def _deliver_messages(self):
        """Receives messages from the MQTT broker and puts them in the internal buffer."""

        message = None

        while not self._event_stop_request.is_set():
            if message is None:
                try:
                    message = await self._client.deliver_message(timeout_duration=self._timeout_loops_secs)
                except asyncio.TimeoutError:
                    pass
                except Exception as ex:
                    self._log(logging.WARNING, "Error on MQTT deliver: {}".format(ex))

                    try:
                        await asyncio.sleep(self._sleep_error_reconnect)
                        await self.connect(force_reconnect=True)
                    except Exception as ex:
                        self._log(logging.ERROR, "Error reconnecting: {}".format(ex), exc_info=True)

            if message is not None:
                try:
                    await asyncio.wait_for(
                        self._messages_buffer.put(message), timeout=self._timeout_loops_secs)
                    message = None
                except asyncio.TimeoutError:
                    self._log(logging.DEBUG, "Full messages buffer")

    async def _handle_messages(self):
        """Gets messages from the internal buffer and
        passes them to the MQTT handler to be processed."""

        while not self._event_stop_request.is_set():
            try:
                message = await asyncio.wait_for(
                    self._messages_buffer.get(), timeout=self._timeout_loops_secs)
                self._log(logging.DEBUG, "Handling message: {}".format(message.data))
                asyncio.ensure_future(self._mqtt_handler.handle_message(message))
            except asyncio.TimeoutError:
                pass
            except Exception as ex:
                self._log(logging.WARNING, "MQTT handler error: {}".format(ex), exc_info=True)

    async def _publish_queued_messages(self):
        """Gets the pending messages from the handler queue and publishes them on the broker."""

        message = None

        while not self._event_stop_request.is_set():
            try:
                if message is None:
                    message = await asyncio.wait_for(
                        self._mqtt_handler.queue.get(), timeout=self._timeout_loops_secs)
                else:
                    self._log(logging.WARNING, "Republish attempt: {}".format(message))

                await self._client.publish(
                    topic=message["topic"],
                    message=message["data"],
                    qos=message.get("qos", None),
                    retain=message.get("retain", None))

                message = None
            except asyncio.TimeoutError:
                pass
            except Exception as ex:
                self._log(logging.WARNING, "Exception publishing: {}".format(ex), exc_info=True)
                await asyncio.sleep(self._sleep_error_reconnect)

    async def _add_loop_callback(self):
        """Adds the callback that will start the infinite loop
        to listen and handle the messages published in the topics
        that are of interest to this MQTT client."""

        try:
            async with self._lock_run:
                self._log(logging.DEBUG, "Entering MQTT runner loop")

                asyncio.ensure_future(self._deliver_messages())
                asyncio.ensure_future(self._handle_messages())
                asyncio.ensure_future(self._publish_queued_messages())

        except asyncio.TimeoutError:
            self._log(
                logging.WARNING,
                "Cannot start MQTT handler loop while another is already running"
            )

    async def start(self):
        """Starts listening for published messages."""

        self._event_stop_request.set()

        async with self._lock_run:
            self._event_stop_request.clear()

        await self.connect(force_reconnect=True)
        await self._mqtt_handler.init()
        await self._add_loop_callback()

    async def stop(self):
        """Stops listening for published messages."""

        self._event_stop_request.set()

        async with self._lock_run:
            pass

        await self._mqtt_handler.teardown()

        await self.disconnect()
