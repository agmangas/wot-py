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
General utilities.
"""

import json

from tornado.web import HTTPError

APPLICATION_JSON = "application/json"


def get_exposed_thing(server, title):
    """Utility function to retrieve an ExposedThing
    from the HTTPServer or raise an HTTPError."""

    try:
        return server.get_exposed_thing(title)
    except ValueError:
        raise HTTPError(reason=f"Unknown Thing: {title}")


def parse_json_body(req_handler):
    """Parses the request body as JSON and returns the resulting object."""

    try:
        parsed_body = json.loads(req_handler.request.body)
    except Exception as ex:
        raise HTTPError(log_message="Error decoding JSON: {}".format(ex))
    return parsed_body


def request_auth(req_handler, scheme, thing_name):
    """If authentication fails request authentication from the client with the correct scheme."""

    req_handler.set_header("WWW-Authenticate", f"{scheme} realm={thing_name}")
    req_handler.set_status(401)
    req_handler.finish()
