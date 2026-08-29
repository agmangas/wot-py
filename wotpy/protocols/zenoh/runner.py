#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2025 National Technical University of Athens
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
Base class for Zenoh handlers.
"""

import asyncio
import logging
import uuid


class ZenohHandlerRunner:
    """Class that wraps a Zenoh handler. It handles connections to the
    Zenoh broker, delivers messages, and runs the handler in a loop."""

    DEFAULT_TIMEOUT_LOOPS_SECS = 0.1
    DEFAULT_SLEEP_ERR_RECONN = 2.0
    DEFAULT_MSGS_BUF_SIZE = 500

    def __init__(self, router_url, zenoh_handler,
                 messages_buffer_size=DEFAULT_MSGS_BUF_SIZE,
                 timeout_loops=DEFAULT_TIMEOUT_LOOPS_SECS,
                 sleep_error_reconnect=DEFAULT_SLEEP_ERR_RECONN):
        self._router_url = router_url
        self._zenoh_handler = zenoh_handler
        self._messages_buffer = asyncio.Queue(maxsize=messages_buffer_size)
        self._timeout_loops_secs = timeout_loops
        self._sleep_error_reconnect = sleep_error_reconnect
        self._subscribers = {}
        self._client_id = uuid.uuid4().hex
        self._lock_run = asyncio.Lock()
        self._event_stop_request = asyncio.Event()
        self._logr = logging.getLogger(__name__)

    def _log(self, level, msg, **kwargs):
        """Helper function to wrap all log messages."""

        self._logr.log(level, "{} - {}".format(self._zenoh_handler.__class__.__name__, msg), **kwargs)

    async def _deliver_messages(self, sample):
        """Receives messages from the Zenoh broker and puts them in the internal buffer."""

        if sample is not None:
            try:
                await asyncio.wait_for(
                    self._messages_buffer.put(sample), timeout=self._timeout_loops_secs)
                sample = None
            except asyncio.TimeoutError:
                self._log(logging.DEBUG, "Full messages buffer")

    async def _handle_messages(self):
        """Gets messages from the internal buffer and
        passes them to the Zenoh handler to be processed."""

        while not self._event_stop_request.is_set():
            try:
                sample = await asyncio.wait_for(
                    self._messages_buffer.get(), timeout=self._timeout_loops_secs)
                self._log(logging.DEBUG, "Handling message: {}".format(sample.payload.to_string()))
                asyncio.ensure_future(self._zenoh_handler.handle_message(sample))
            except asyncio.TimeoutError:
                pass
            except Exception as ex:
                self._log(logging.WARNING, "Zenoh handler error: {}".format(ex), exc_info=True)

    async def _publish_queued_messages(self):
        """Gets the pending messages from the handler queue and publishes them on the broker."""

        message = None

        while not self._event_stop_request.is_set():
            try:
                if message is None:
                    message = await asyncio.wait_for(
                        self._zenoh_handler.queue.get(), timeout=self._timeout_loops_secs)
                else:
                    self._log(logging.WARNING, "Republish attempt: {}".format(message))

                session = self._zenoh_handler._zenoh_server._session
                session.put(
                    key_expr=message["topic"],
                    payload=message["data"]
                )

                message = None
            except asyncio.TimeoutError:
                pass
            except Exception as ex:
                self._log(logging.WARNING, "Exception publishing: {}".format(ex), exc_info=True)
                await asyncio.sleep(self._sleep_error_reconnect)

    async def _subscribe(self):
        """Subscribes to the runner's topics."""

        async with self._lock_run:
            loop = asyncio.get_running_loop()

            # Zenoh callbacks run on a different thread. Using asyncio.run() would
            # create a different loop that creates overhead
            def listener(sample):
                coro = self._deliver_messages(sample)
                asyncio.run_coroutine_threadsafe(coro, loop)

            if self._zenoh_handler.topics:
                self._log(logging.DEBUG, "Subscribing to: {}".format(self._zenoh_handler.topics))
                for topic in self._zenoh_handler.topics:
                    session = self._zenoh_handler._zenoh_server._session
                    self._subscribers[topic] = session.declare_subscriber(topic, listener)

    def _add_loop_callback(self):
        """Adds the callback that will start the infinite loop
        to listen and handle the messages published in the topics
        that are of interest to this Zenoh client."""

        async def run_loop():
            try:
                async with self._lock_run:
                    self._log(logging.DEBUG, "Entering Zenoh runner loop")
                    asyncio.ensure_future(self._handle_messages())
                    asyncio.ensure_future(self._publish_queued_messages())
            except asyncio.TimeoutError:
                self._log(logging.WARNING, "Cannot start Zenoh handler loop while another is already running")

        asyncio.create_task(run_loop())

    async def start(self):
        """Starts listening for published messages."""

        self._event_stop_request.set()

        async with self._lock_run:
            self._event_stop_request.clear()

        await self._zenoh_handler.init()
        await self._subscribe()

        self._add_loop_callback()

    async def stop(self):
        """Stops listening for published messages."""

        self._event_stop_request.set()

        for subscriber in self._subscribers.values():
            subscriber.undeclare()
        self._subscribers = {}

        async with self._lock_run:
            pass

        await self._zenoh_handler.teardown()
