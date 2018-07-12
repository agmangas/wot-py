#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Action interactions.
"""

import uuid

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
        future_result = exposed_thing.actions[name].run(input_value)
        invocation_id = uuid.uuid4().hex
        self._server.pending_actions[invocation_id] = future_result
        self.write({"invocation": "/invocation/{}".format(invocation_id)})


# noinspection PyAbstractClass,PyAttributeOutsideInit
class PendingInvocationHandler(RequestHandler):
    """Handler to check the status of pending action invocations."""

    # noinspection PyMethodOverriding
    def initialize(self, http_server):
        self._server = http_server

    @tornado.gen.coroutine
    def get(self, invocation_id):
        """Checks and returns the status of the Future that represents an action invocation."""

        if invocation_id not in self._server.pending_actions:
            raise HTTPError(log_message="Unknown invocation: {}".format(invocation_id))

        future_result = self._server.pending_actions[invocation_id]

        if not future_result.done():
            self.write({"done": False})
            return

        try:
            result = future_result.result()
            self.write({"done": True, "result": result})
        except Exception as ex:
            self.write({"done": True, "error": str(ex)})
        finally:
            self._server.pending_actions.pop(invocation_id)
