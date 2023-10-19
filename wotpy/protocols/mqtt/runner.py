#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class for MQTT handlers.
"""

import asyncio
import copy
import logging
import uuid
from asyncio import Queue

import aiomqtt

from wotpy.protocols.mqtt.utils import MQTTBrokerURL, aiomqtt_read_loop


class MQTTHandlerRunner(object):
    """Class that wraps an MQTT handler. It handles connections to the
    MQTT broker, delivers messages, and runs the handler in a loop."""

    DEFAULT_TIMEOUT_LOOPS_SECS = 0.1
    DEFAULT_SLEEP_ERR_RECONN = 2.0
    DEFAULT_MSGS_BUF_SIZE = 500

    DEFAULT_CLIENT_CONFIG = {"clean_session": False}

    def __init__(
        self,
        broker_url,
        mqtt_handler,
        messages_buffer_size=DEFAULT_MSGS_BUF_SIZE,
        timeout_loops=DEFAULT_TIMEOUT_LOOPS_SECS,
        sleep_error_reconnect=DEFAULT_SLEEP_ERR_RECONN,
        aiomqtt_config=None,
    ):
        self._broker_url = broker_url
        self._mqtt_handler = mqtt_handler
        self._messages_buffer = Queue(maxsize=messages_buffer_size)
        self._timeout_loops_secs = timeout_loops
        self._sleep_error_reconnect = sleep_error_reconnect
        self._aiomqtt_config = aiomqtt_config
        self._client = None
        self._client_id = uuid.uuid4().hex
        self._lock_conn = asyncio.Lock()
        self._lock_run = asyncio.Lock()
        self._event_stop_request = asyncio.Event()
        self._logr = logging.getLogger(__name__)
        self._run_loop_task = None

    def _log(self, level, msg, **kwargs):
        """Helper function to wrap all log messages."""

        self._logr.log(
            level,
            "{} - {}".format(self._mqtt_handler.__class__.__name__, msg),
            **kwargs
        )

    def _build_client_config(self):
        """Returns the config dict for a new MQTT client instance."""

        config = copy.copy(self.DEFAULT_CLIENT_CONFIG)
        config.update(self._aiomqtt_config if self._aiomqtt_config else {})
        mqtt_broker_url = MQTTBrokerURL.from_url(self._broker_url)

        config.update(
            {
                "hostname": mqtt_broker_url.host,
                "port": mqtt_broker_url.port,
                "username": mqtt_broker_url.username,
                "password": mqtt_broker_url.password,
                "client_id": self._client_id,
            }
        )

        return config

    async def _connect(self):
        """MQTT connection helper function."""

        config = self._build_client_config()
        self._log(logging.DEBUG, "MQTT client config: {}".format(config))
        aiomqtt_client = aiomqtt.Client(**config)
        await aiomqtt_client.__aenter__()

        if self._mqtt_handler.topics:
            self._log(
                logging.DEBUG, "Subscribing to: {}".format(self._mqtt_handler.topics)
            )

            await asyncio.gather(
                *[
                    aiomqtt_client.subscribe(topic=topic, qos=qos)
                    for topic, qos in self._mqtt_handler.topics
                ]
            )

        self._client = aiomqtt_client

    async def _disconnect(self):
        """MQTT disconnection helper function."""

        try:
            self._log(logging.DEBUG, "Disconnecting MQTT client")
            await self._client.__aexit__(exc_type=None, exc=None, tb=None)
        except Exception as ex:
            self._log(
                logging.DEBUG,
                "Error disconnecting MQTT client: {}".format(ex),
                exc_info=True,
            )
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

        async def anext_ex_handler(ex: Exception):
            self._log(
                logging.WARNING,
                "Error reading MQTT queue ({}): {}".format(ex.__class__, ex),
            )

            try:
                await asyncio.sleep(self._sleep_error_reconnect)
                await self.connect(force_reconnect=True)
            except Exception as ex:
                self._log(
                    logging.ERROR,
                    "Error reconnecting: {}".format(ex),
                    exc_info=True,
                )

        async def message_handler(message: aiomqtt.Message):
            try:
                await asyncio.wait_for(
                    self._messages_buffer.put(message),
                    timeout=self._timeout_loops_secs,
                )
            except asyncio.TimeoutError:
                self._log(logging.DEBUG, "Full messages buffer")

        await aiomqtt_read_loop(
            stop_event=self._event_stop_request,
            client=self._client,
            anext_ex_handler=anext_ex_handler,
            message_handler=message_handler,
        )

    async def _handle_messages(self):
        """Gets messages from the internal buffer and
        passes them to the MQTT handler to be processed."""

        while not self._event_stop_request.is_set():
            try:
                message = await asyncio.wait_for(
                    self._messages_buffer.get(), timeout=self._timeout_loops_secs
                )
                self._log(logging.DEBUG, "Handling message: {}".format(message.payload))
                await self._mqtt_handler.handle_message(message)
            except asyncio.TimeoutError:
                pass
            except Exception as ex:
                self._log(
                    logging.WARNING, "MQTT handler error: {}".format(ex), exc_info=True
                )

    async def _publish_queued_messages(self):
        """Gets the pending messages from the handler queue and publishes them on the broker."""

        message = None

        while not self._event_stop_request.is_set():
            try:
                if message is None:
                    message = await asyncio.wait_for(
                        self._mqtt_handler.queue.get(), timeout=self._timeout_loops_secs
                    )
                else:
                    self._log(logging.WARNING, "Republish attempt: {}".format(message))

                await self._client.publish(
                    topic=message["topic"],
                    payload=message["data"],
                    qos=message.get("qos", 0),
                    retain=message.get("retain", False),
                )

                message = None
            except asyncio.TimeoutError:
                pass
            except Exception as ex:
                self._log(
                    logging.WARNING,
                    "Exception publishing: {}".format(ex),
                    exc_info=True,
                )
                await asyncio.sleep(self._sleep_error_reconnect)

    async def _run_loop(self):
        """Adds the callback that will start the infinite loop
        to listen and handle the messages published in the topics
        that are of interest to this MQTT client."""

        try:
            async with self._lock_run:
                self._log(logging.DEBUG, "Entering MQTT runner loop")

                await asyncio.gather(
                    self._deliver_messages(),
                    self._handle_messages(),
                    self._publish_queued_messages(),
                )
        except asyncio.TimeoutError:
            self._log(
                logging.WARNING,
                "Cannot start MQTT handler loop while another is already running",
            )

    async def start(self):
        """Starts listening for published messages."""

        self._event_stop_request.set()

        async with self._lock_run:
            self._event_stop_request.clear()

        await self.connect(force_reconnect=True)
        await self._mqtt_handler.init()
        self._run_loop_task = asyncio.create_task(self._run_loop())

    async def stop(self, run_loop_timeout=60.0):
        """Stops listening for published messages."""

        self._event_stop_request.set()

        async with self._lock_run:
            pass

        await self._mqtt_handler.teardown()

        try:
            await asyncio.wait_for(self._run_loop_task, timeout=run_loop_timeout)
        except asyncio.TimeoutError:
            self._log(logging.WARNING, "MQTT handler loop did not finish in time")

        await self.disconnect()
