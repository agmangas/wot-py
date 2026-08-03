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
Request handler for Action interactions.
"""

from tornado.web import RequestHandler

import wotpy.protocols.http.handlers.utils as handler_utils


class ActionInvokeHandler(RequestHandler):
    """Handler for Action invocation requests."""

    def initialize(self, http_server):
        self._server = http_server

    async def post(self, thing_name, name):
        """Invokes the action and returns the invocation result."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        valid_creds = await self._server._check_credentials(exposed_thing.title, self.request)
        if not valid_creds:
            handler_utils.request_auth(self, self._server.security_scheme, thing_name)
        else:
            input_value = handler_utils.get_argument(self, "input")
            try:
                result = await exposed_thing.actions[name].invoke(input_value)
                self.write({"result": result})
            except Exception as ex:
                self.write({"error": str(ex)})
