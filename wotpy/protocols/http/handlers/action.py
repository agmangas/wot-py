#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Action interactions.
"""

import logging
import pprint
import time
import uuid

import six
import tornado.gen
from tornado.web import HTTPError
from tornado.web import RequestHandler

import wotpy.protocols.http.handlers.utils as handler_utils


# noinspection PyAbstractClass,PyAttributeOutsideInit
class ActionInvokeHandler(RequestHandler):
    """Handler for Action invocation requests."""

    # noinspection PyMethodOverriding
    def initialize(self, http_server):
        self._server = http_server

    @tornado.gen.coroutine
    def post(self, thing_name, name):
        """Invokes the action and returns the invocation result."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        input_value = handler_utils.get_argument(self, "input")
        future_result = exposed_thing.actions[name].invoke(input_value)
        invocation_id = uuid.uuid4().hex
        self._server.pending_actions[invocation_id] = future_result
        self.write({"invocation": "/invocation/{}".format(invocation_id)})


# noinspection PyAbstractClass,PyAttributeOutsideInit
class PendingInvocationHandler(RequestHandler):
    """Handler to check the status of pending action invocations."""

    # noinspection PyMethodOverriding
    def initialize(self, http_server):
        self._server = http_server
        self._logr = logging.getLogger(__name__)

    def _clean_expired(self):
        """Removes the Action invocations that are expired and
        have already been checked by at least one client."""

        now = time.time()

        expired_invocations = [
            inv_id for inv_id, tstamp in six.iteritems(self._server.invocation_check_times)
            if (now - tstamp) > self._server.action_ttl
        ]

        if len(expired_invocations):
            self._logr.debug("Expired invocations: {}".format(pprint.pformat(expired_invocations)))

        for invocation_id in expired_invocations:
            self._server.invocation_check_times.pop(invocation_id)
            fut_result = self._server.pending_actions.get(invocation_id, None)

            if fut_result and fut_result.done():
                self._logr.debug("Removing completed invocation Future: {}".format(invocation_id))
                self._server.pending_actions.pop(invocation_id, None)

    @tornado.gen.coroutine
    def get(self, invocation_id):
        """Checks and returns the status of the Future that represents an action invocation."""

        if invocation_id not in self._server.pending_actions:
            raise HTTPError(log_message="Unknown invocation: {}".format(invocation_id))

        try:
            result = yield self._server.pending_actions[invocation_id]
            self.write({"done": True, "result": result})
        except Exception as ex:
            self.write({"done": True, "error": str(ex)})
        finally:
            self._logr.debug("Updating invocation check time: {}".format(invocation_id))
            self._server.invocation_check_times[invocation_id] = time.time()
            self._clean_expired()
