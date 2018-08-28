#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP resources to deal with Property interactions.
"""

import json

import aiocoap
import aiocoap.error
import aiocoap.resource
import tornado.gen

JSON_CONTENT_FORMAT = 50


@tornado.gen.coroutine
def _build_property_value_response(thing_property):
    """Reads the current property value and builds
    the CoAP response containing said value."""

    value = yield thing_property.read()
    payload = json.dumps({"value": value}).encode("utf-8")
    response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=payload)
    response.opt.content_format = JSON_CONTENT_FORMAT
    raise tornado.gen.Return(response)


class PropertyReadWriteResource(aiocoap.resource.Resource):
    """CoAP resource to handle Property reads and writes."""

    def __init__(self, exposed_thing, name):
        super(PropertyReadWriteResource, self).__init__()
        self._exposed_thing = exposed_thing
        self._name = name

    # noinspection PyUnusedLocal
    @tornado.gen.coroutine
    def render_get(self, request):
        """Returns a CoAP response with the current property value."""

        response = yield _build_property_value_response(self._exposed_thing.properties[self._name])
        raise tornado.gen.Return(response)

    @tornado.gen.coroutine
    def render_post(self, request):
        """Updates the property with the value retrieved from the CoAP request payload."""

        request_payload = json.loads(request.payload)

        if "value" not in request_payload:
            raise aiocoap.error.BadRequest()

        yield self._exposed_thing.properties[self._name].write(request_payload.get("value"))
        response = aiocoap.Message(code=aiocoap.Code.CHANGED)

        raise tornado.gen.Return(response)


class PropertyObservableResource(aiocoap.resource.ObservableResource):
    """CoAP resource to observe property updates."""

    def __init__(self, exposed_thing, name):
        super(PropertyObservableResource, self).__init__()
        self._exposed_thing = exposed_thing
        self._name = name
        self._subscription = None

    def update_observation_count(self, count):
        """Hook into this method to be notified when the
        number of observations on the resource changes."""

        # noinspection PyUnusedLocal
        def on_next(item):
            self.updated_state()

        if count > 0 and self._subscription is None:
            self._subscription = self._exposed_thing.properties[self._name].subscribe(on_next)
        elif count == 0 and self._subscription is not None:
            self._subscription.dispose()
            self._subscription = None

    # noinspection PyUnusedLocal
    @tornado.gen.coroutine
    def render_get(self, request):
        """Returns a CoAP response with the current property value."""

        response = yield _build_property_value_response(self._exposed_thing.properties[self._name])
        raise tornado.gen.Return(response)
