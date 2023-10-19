#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP resources to deal with Property interactions.
"""

import json
import logging

import aiocoap
import aiocoap.error
import aiocoap.resource

from wotpy.protocols.coap.resources.utils import parse_request_opt_query

JSON_CONTENT_FORMAT = 50


async def _build_property_value_response(thing_property):
    """Reads the current property value and builds
    the CoAP response containing said value."""

    value = await thing_property.read()
    payload = json.dumps({"value": value}).encode("utf-8")
    response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=payload)
    response.opt.content_format = JSON_CONTENT_FORMAT
    return response


def get_thing_property(server, request):
    """Takes a CoAP request and returns the Thing Property
    identified by the request arguments."""

    query = parse_request_opt_query(request)
    url_name_thing = query.get("thing")
    url_name_prop = query.get("name")

    if not url_name_thing or not url_name_prop:
        raise aiocoap.error.BadRequest("Missing query arguments")

    exposed_thing = server.exposed_thing_set.find_by_thing_id(url_name_thing)

    if not exposed_thing:
        raise aiocoap.error.NotFound("Thing not found")

    try:
        return next(
            exposed_thing.properties[key]
            for key in exposed_thing.properties
            if exposed_thing.properties[key].url_name == url_name_prop
        )
    except StopIteration:
        raise aiocoap.error.NotFound("Property not found") from None


class PropertyResource(aiocoap.resource.ObservableResource):
    """CoAP resource that implements the Property read, write and observe verbs."""

    def __init__(self, server):
        super(PropertyResource, self).__init__()
        self._server = server
        self._logr = logging.getLogger(__name__)

    async def add_observation(self, request, server_observation):
        """Method that decides whether to add a new observer.
        A new observer is added for each GET request."""

        if request.code.name != aiocoap.Code.GET.name:
            return

        try:
            thing_property = get_thing_property(self._server, request)
        except aiocoap.error.Error:
            return

        def on_next(item):
            server_observation.trigger()

        def on_error(err):
            self._logr.warning(
                "Error on subscription to {}: {}".format(thing_property, err)
            )

        subscription = thing_property.subscribe(on_next=on_next, on_error=on_error)

        def cancellation_cb():
            self._logr.debug("Disposing of subscription to: {}".format(thing_property))
            subscription.dispose()

        server_observation.accept(cancellation_cb)

    async def render_get(self, request):
        """Returns a CoAP response with the current property value."""

        thing_property = get_thing_property(self._server, request)
        response = await _build_property_value_response(thing_property)
        return response

    async def render_put(self, request):
        """Updates the property with the value retrieved from the CoAP request payload."""

        thing_property = get_thing_property(self._server, request)
        request_payload = json.loads(request.payload)

        if "value" not in request_payload:
            raise aiocoap.error.BadRequest()

        await thing_property.write(request_payload.get("value"))
        response = aiocoap.Message(code=aiocoap.Code.CHANGED)

        return response
