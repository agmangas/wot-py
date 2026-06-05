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
Request handler for Action interactions.
"""

import logging
import pprint
import time
import uuid

from tornado.web import HTTPError, RequestHandler

import wotpy.protocols.http.handlers.utils as handler_utils


class ActionInvokeHandler(RequestHandler):
    """Handler for Action invocation requests."""

    def initialize(self, http_server):
        self._server = http_server

    async def post(self, thing_name, name):
        """Invokes the action and returns the invocation result."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        input_value = handler_utils.get_argument(self, "input")
        future_result = exposed_thing.actions[name].invoke(input_value)
        invocation_id = uuid.uuid4().hex
        self._server.pending_actions[invocation_id] = future_result
        self.write({"invocation": "/invocation/{}".format(invocation_id)})


class PendingInvocationHandler(RequestHandler):
    """Handler to check the status of pending action invocations."""

    def initialize(self, http_server):
        self._server = http_server
        self._logr = logging.getLogger(__name__)

    def _clean_expired(self):
        """Removes the Action invocations that are expired and
        have already been checked by at least one client."""

        now = time.time()

        expired_invocations = [
            inv_id
            for inv_id, tstamp in self._server.invocation_check_times.items()
            if (now - tstamp) > self._server.action_ttl
        ]

        if len(expired_invocations):
            self._logr.debug(
                "Expired invocations: {}".format(pprint.pformat(expired_invocations))
            )

        for invocation_id in expired_invocations:
            self._server.invocation_check_times.pop(invocation_id)
            fut_result = self._server.pending_actions.get(invocation_id, None)

            if fut_result and fut_result.done():
                self._logr.debug(
                    "Removing completed invocation Future: {}".format(invocation_id)
                )

                self._server.pending_actions.pop(invocation_id, None)

    async def get(self, invocation_id):
        """Checks and returns the status of the Future that represents an action invocation."""

        if invocation_id not in self._server.pending_actions:
            raise HTTPError(log_message="Unknown invocation: {}".format(invocation_id))

        try:
            result = await self._server.pending_actions[invocation_id]
            self.write({"done": True, "result": result})
        except Exception as ex:
            self.write({"done": True, "error": str(ex)})
        finally:
            self._logr.debug("Updating invocation check time: {}".format(invocation_id))
            self._server.invocation_check_times[invocation_id] = time.time()
            self._clean_expired()
