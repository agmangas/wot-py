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


class PropertyReadWriteResource(aiocoap.resource.Resource):
    """CoAP resource to handle Property reads and writes."""

    JSON_CONTENT_FORMAT = 50
    ENCODING = "utf-8"

    def __init__(self, exposed_thing, name):
        super(PropertyReadWriteResource, self).__init__()
        self._exposed_thing = exposed_thing
        self._name = name

    # noinspection PyUnusedLocal
    @tornado.gen.coroutine
    def render_get(self, request):
        """Returns a CoAP response with the current property value."""

        value = yield self._exposed_thing.properties[self._name].read()
        payload = json.dumps({"value": value}).encode(self.ENCODING)
        response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=payload)
        response.opt.content_format = self.JSON_CONTENT_FORMAT

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
