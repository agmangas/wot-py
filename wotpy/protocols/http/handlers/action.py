#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Action interactions.
"""

import tornado.gen
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
        result = yield exposed_thing.actions[name].run(input_value)
        self.write({"result": result})
