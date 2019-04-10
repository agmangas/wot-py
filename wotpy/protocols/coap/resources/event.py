#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP resources to deal with Event interactions.
"""

import json
import logging
import time

import aiocoap
import aiocoap.error
import aiocoap.resource
import tornado.gen

from wotpy.protocols.coap.resources.utils import parse_request_opt_query

JSON_CONTENT_FORMAT = 50


def get_thing_event(server, request):
    """Takes a CoAP request and returns the Thing Event
    identified by the request arguments."""

    query = parse_request_opt_query(request)
    url_name_thing = query.get("thing")
    url_name_event = query.get("name")

    if not url_name_thing or not url_name_event:
        raise aiocoap.error.BadRequest("Missing query arguments")

    exposed_thing = server.exposed_thing_set.find_by_thing_id(url_name_thing)

    if not exposed_thing:
        raise aiocoap.error.NotFound("Thing not found")

    try:
        return next(
            exposed_thing.events[key] for key in exposed_thing.events
            if exposed_thing.events[key].url_name == url_name_event)
    except StopIteration:
        raise aiocoap.error.NotFound("Event not found")


class EventResource(aiocoap.resource.ObservableResource):
    """CoAP resource to observe Event emissions."""

    def __init__(self, server):
        super(EventResource, self).__init__()
        self._server = server
        self._subscription = None
        self._last_events = {}
        self._logr = logging.getLogger(__name__)

    @classmethod
    def _event_key(cls, thing_event):
        """Returns the internal event key for the given Thing Event."""

        return thing_event.thing.url_name, thing_event.url_name

    @tornado.gen.coroutine
    def add_observation(self, request, server_observation):
        """Method that decides whether to add a new observer.
        A new observer is added for each GET request."""

        if request.code.name != aiocoap.Code.GET.name:
            return

        try:
            thing_event = get_thing_event(self._server, request)
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

    @tornado.gen.coroutine
    def render_get(self, request):
        """Returns a CoAP response with the last observed event emission."""

        thing_event = get_thing_event(self._server, request)
        last_item = self._last_events.get(self._event_key(thing_event), None)
        payload = json.dumps(last_item).encode("utf-8") if last_item else b""
        response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=payload)
        response.opt.content_format = JSON_CONTENT_FORMAT

        raise tornado.gen.Return(response)
