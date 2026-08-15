#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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
Request handler for Property interactions.
"""

import asyncio
import logging

from tornado.web import HTTPError

import wotpy.protocols.http.handlers.utils as handler_utils
from wotpy.protocols.http.handlers.base import BaseHandler


class PropertyReadWriteHandler(BaseHandler):
    """Handler for Property get/set requests."""

    def initialize(self, http_server):
        self._server = http_server

    async def get(self, thing_name, name):
        """Reads and returns the Property value."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        valid_creds = await self._server._check_credentials(exposed_thing.title, self.request)
        if not valid_creds:
            handler_utils.request_auth(self, self._server.security_scheme, thing_name)
        else:
            value = await exposed_thing.properties[name].read()
            self.write({"value": value})

    async def put(self, thing_name, name):
        """Updates the Property value."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        valid_creds = await self._server._check_credentials(exposed_thing.title, self.request)
        if not valid_creds:
            handler_utils.request_auth(self, self._server.security_scheme, thing_name)
        else:
            value = handler_utils.get_argument(self, "value", self.request.body)
            try:
                await exposed_thing.handle_write_property(name, value)
            except TypeError as ex:
                raise HTTPError(reason=str(ex))


class PropertyObserverHandler(BaseHandler):
    """Handler for Property subscription requests."""

    def initialize(self, http_server):
        self._server = http_server
        self._logr = logging.getLogger(__name__)

    async def get(self, thing_name, name):
        """Subscribes to Property updates and waits for the next event (HTTP long-polling pattern).
        Returns the updated value and destroys the subscription."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        valid_creds = await self._server._check_credentials(exposed_thing.title, self.request)
        if not valid_creds:
            handler_utils.request_auth(self, self._server.security_scheme, thing_name)
        else:
            thing_property = exposed_thing.properties[name]

            loop = asyncio.get_running_loop()
            future_next = loop.create_future()

            def on_next(item):
                not future_next.done() and future_next.set_result(item.data.value)

            def on_error(err):
                self._logr.warning("Error on subscription to {}: {}".format(thing_property, err))
                not future_next.done() and future_next.set_exception(err)

            self.subscription = thing_property.subscribe(on_next=on_next, on_error=on_error)
            updated_value = await future_next
            self.write({"value": updated_value})

    def on_finish(self):
        """Destroys the subscription to the observable when the request finishes."""

        try:
            self.subscription.dispose()
        except AttributeError:
            pass
