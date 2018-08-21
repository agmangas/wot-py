#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP resources to deal with Property interactions.
"""

import aiocoap
import aiocoap.resource as resource
import tornado.gen


class PropertyReadWriteResource(resource.Resource):
    """CoAP resource to handle Property reads and writes."""

    def __init__(self, server):
        super(PropertyReadWriteResource, self).__init__()
        self._server = server

    @tornado.gen.coroutine
    def render_get(self, request):
        return aiocoap.Message(payload=b"Hello World!")
