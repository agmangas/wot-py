#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class for all Zenoh handlers.
"""

import asyncio


class BaseZenohHandler:
    """Base class for all Zenoh handlers."""

    def __init__(self, zenoh_server):
        self._zenoh_server = zenoh_server
        self._queue = asyncio.Queue()
        self._subscriber = None

    @property
    def servient_id(self):
        """Servient ID that is used to avoid topic collisions
        when multiple Servients are connected to the same broker."""

        return self._zenoh_server.servient_id

    @property
    def zenoh_server(self):
        """Zenoh server that contains this handler."""

        return self._zenoh_server

    @property
    def topics(self):
        """List of topics that this Zenoh handler wants to subscribe to."""

        return None

    @property
    def queue(self):
        """Asynchronous queue where the handler leaves messages
        that should be published later by the runner."""

        return self._queue

    @property
    def subscriber(self):
        """Zenoh Subscriber that can be used to fetch
        queued messages."""

        return self._subscriber

    async def handle_message(self, sample):
        """Called each time the runner receives a message for one of the handler topics."""

        pass

    async def init(self):
        """Initializes the Zenoh handler.
        Called when the Zenoh runner starts."""

        pass

    async def teardown(self):
        """Destroys the Zenoh handler.
        Called when the Zenoh runner stops."""

        pass
