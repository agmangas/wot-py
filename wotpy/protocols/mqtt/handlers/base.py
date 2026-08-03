#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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
Base class for all MQTT handlers.
"""

import asyncio


class BaseMQTTHandler:
    """Base class for all MQTT handlers."""

    def __init__(self, mqtt_server):
        self._mqtt_server = mqtt_server
        self._queue = asyncio.Queue()

    @property
    def servient_id(self):
        """Servient ID that is used to avoid topic collisions
        when multiple Servients are connected to the same broker."""

        return self._mqtt_server.servient_id

    @property
    def mqtt_server(self):
        """MQTT server that contains this handler."""

        return self._mqtt_server

    @property
    def topics(self):
        """List of topics that this MQTT handler wants to subscribe to."""

        return None

    @property
    def queue(self):
        """Asynchronous queue where the handler leaves messages
        that should be published later by the runner."""

        return self._queue

    async def handle_message(self, msg):
        """Called each time the runner receives a message for one of the handler topics."""

        pass

    async def init(self):
        """Initializes the MQTT handler.
        Called when the MQTT runner starts."""

        pass

    async def teardown(self):
        """Destroys the MQTT handler.
        Called when the MQTT runner stops."""

        pass
