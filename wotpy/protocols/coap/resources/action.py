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
CoAP resources to deal with Action interactions.
"""

import asyncio
import json
import logging
import uuid

import aiocoap
import aiocoap.error
import aiocoap.resource

from wotpy.protocols.coap.resources.utils import parse_request_opt_query

JSON_CONTENT_FORMAT = 50


async def get_thing_action(server, request):
    """Takes a CoAP request and returns the Thing Action
    identified by the request arguments."""

    query = parse_request_opt_query(request)
    url_name_thing = query.get("thing")
    url_name_action = query.get("name")

    if not url_name_thing or not url_name_action:
        raise aiocoap.error.BadRequest("Missing query arguments")

    exposed_thing = server.exposed_thing_set.find_by_thing_title(url_name_thing)

    if not exposed_thing:
        raise aiocoap.error.NotFound("Thing not found")

    valid_creds = await server._check_credentials(exposed_thing.title, request)
    if not valid_creds:
        raise aiocoap.error.Unauthorized("Authentication required")

    try:
        return next(
            exposed_thing.actions[key] for key in exposed_thing.actions
            if exposed_thing.actions[key].url_name == url_name_action)
    except StopIteration:
        raise aiocoap.error.NotFound("Action not found")


class ActionResource(aiocoap.resource.ObservableResource):
    """CoAP resource to invoke Actions and observe those invocations."""


    def __init__(self, server):
        super().__init__()
        self._server = server
        self._logr = logging.getLogger(__name__)

    async def render_post(self, request):
        """Handler for action invocations."""

        thing_action = await get_thing_action(self._server, request)

        self._logr.debug("Action POST request: {}".format(thing_action))

        request_payload = json.loads(request.payload)

        try:
            result = await thing_action.invoke(request_payload)
            response_payload = json.dumps(result).encode("utf-8")
        except Exception as ex:
            self._logr.exception("Error invoking action")
            response_payload = json.dumps(f"error {str(ex)}").encode("utf-8")

        response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=response_payload)
        response.opt.content_format = JSON_CONTENT_FORMAT

        return response
