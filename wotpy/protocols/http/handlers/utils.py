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
Request handler for Property interactions.
"""

import json

from tornado.web import HTTPError

APPLICATION_JSON = "application/json"


def get_exposed_thing(server, thing_name):
    """Utility function to retrieve an ExposedThing
    from the HTTPServer or raise an HTTPError."""

    try:
        return server.get_exposed_thing(thing_name)
    except ValueError:
        raise HTTPError(log_message="Unknown Thing: {}".format(thing_name))


def get_argument(req_handler, name, default=None):
    """Returns an argument extracted from the request.
    Interprets the body as JSON if the Content-Type is application/json.
    Reverts to the default Tornado get_argument otherwise."""

    if req_handler.request.headers.get("Content-Type") != APPLICATION_JSON:
        return req_handler.get_argument(name, default)

    try:
        parsed_body = json.loads(req_handler.request.body)
    except Exception as ex:
        raise HTTPError(log_message="Error decoding JSON: {}".format(ex))

    if not isinstance(parsed_body, dict):
        raise HTTPError(log_message="Not a JSON object: {}".format(parsed_body))

    return parsed_body.get(name, default)
