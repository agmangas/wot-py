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
Request handler for Event interactions.
"""

import asyncio
import logging

from tornado.web import RequestHandler

import wotpy.protocols.http.handlers.utils as handler_utils


class EventObserverHandler(RequestHandler):
    """Handler for Event subscription requests."""

    def initialize(self, http_server):
        self._server = http_server
        self._logr = logging.getLogger(__name__)

    async def get(self, thing_name, name):
        """Subscribes to the given Event and waits for the next emission (HTTP long-polling pattern).
        Returns the event emission payload and destroys the subscription afterwards."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        valid_creds = await self._server._check_credentials(exposed_thing.title, self.request)
        if not valid_creds:
            handler_utils.request_auth(self, self._server.security_scheme, thing_name)
        else:
            thing_event = exposed_thing.events[name]

            loop = asyncio.get_running_loop()
            future_next = loop.create_future()

            def on_next(item):
                not future_next.done() and future_next.set_result(item.data)

            def on_error(err):
                self._logr.warning("Error on subscription to {}: {}".format(thing_event, err))
                not future_next.done() and future_next.set_exception(err)

            self.subscription = thing_event.subscribe(on_next=on_next, on_error=on_error)
            event_payload = await future_next
            self.write({"payload": event_payload})

    def on_finish(self):
        """Destroys the subscription to the observable when the request finishes."""

        try:
            self.subscription.dispose()
        except AttributeError:
            pass
