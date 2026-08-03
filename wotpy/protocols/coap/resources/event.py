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
CoAP resources to deal with Event interactions.
"""

import json
import logging
import time

import aiocoap
import aiocoap.error
import aiocoap.resource

from wotpy.protocols.coap.resources.utils import parse_request_opt_query

JSON_CONTENT_FORMAT = 50


async def get_thing_event(server, request):
    """Takes a CoAP request and returns the Thing Event
    identified by the request arguments."""

    query = parse_request_opt_query(request)
    url_name_thing = query.get("thing")
    url_name_event = query.get("name")

    if not url_name_thing or not url_name_event:
        raise aiocoap.error.BadRequest("Missing query arguments")

    exposed_thing = server.exposed_thing_set.find_by_thing_title(url_name_thing)

    if not exposed_thing:
        raise aiocoap.error.NotFound("Thing not found")

    valid_creds = await server._check_credentials(exposed_thing.title, request)
    if not valid_creds:
        raise aiocoap.error.Unauthorized("Authentication required")

    try:
        return next(
            exposed_thing.events[key] for key in exposed_thing.events
            if exposed_thing.events[key].url_name == url_name_event)
    except StopIteration:
        raise aiocoap.error.NotFound("Event not found")


class EventResource(aiocoap.resource.ObservableResource):
    """CoAP resource to observe Event emissions."""

    def __init__(self, server):
        super().__init__()
        self._server = server
        self._subscription = None
        self._last_events = {}
        self._logr = logging.getLogger(__name__)

    @classmethod
    def _event_key(cls, thing_event):
        """Returns the internal event key for the given Thing Event."""

        return thing_event.thing.url_name, thing_event.url_name

    async def add_observation(self, request, server_observation):
        """Method that decides whether to add a new observer.
        A new observer is added for each GET request."""

        if request.code.name != aiocoap.Code.GET.name:
            return

        try:
            thing_event = await get_thing_event(self._server, request)
        except aiocoap.error.Error:
            return

        def on_next(item):
            event_item = {
                "name": item.name,
                "data": item.data,
                "time": int(time.time() * 1000)
            }

            self._last_events[self._event_key(thing_event)] = event_item
            server_observation.trigger()

        def on_error(err):
            self._logr.warning("Error on subscription to {}: {}".format(thing_event, err))

        subscription = thing_event.subscribe(on_next=on_next, on_error=on_error)

        def cancellation_cb():
            self._logr.debug("Disposing of subscription to: {}".format(thing_event))
            subscription.dispose()

        server_observation.accept(cancellation_cb)

    async def render_get(self, request):
        """Returns a CoAP response with the last observed event emission."""

        thing_event = await get_thing_event(self._server, request)
        last_item = self._last_events.get(self._event_key(thing_event), None)
        payload = json.dumps(last_item).encode("utf-8") if last_item else b""
        response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=payload)
        response.opt.content_format = JSON_CONTENT_FORMAT

        return response
