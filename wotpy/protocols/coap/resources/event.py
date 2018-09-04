#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP resources to deal with Event interactions.
"""

import json
import time

import aiocoap
import aiocoap.error
import aiocoap.resource
import tornado.gen

JSON_CONTENT_FORMAT = 50


class EventObserveResource(aiocoap.resource.ObservableResource):
    """CoAP resource to observe Event emissions."""

    def __init__(self, exposed_thing, name):
        super(EventObserveResource, self).__init__()
        self._exposed_thing = exposed_thing
        self._name = name
        self._subscription = None
        self._last_item = None

    def update_observation_count(self, count):
        """Hook into this method to be notified when the
        number of observations on the resource changes."""

        # noinspection PyUnusedLocal
        def on_next(item):
            self._last_item = {
                "name": item.name,
                "data": item.data,
                "time": int(time.time() * 1000)
            }

            self.updated_state()

        if count > 0 and self._subscription is None:
            self._subscription = self._exposed_thing.events[self._name].subscribe(on_next)
        elif count == 0 and self._subscription is not None:
            self._subscription.dispose()
            self._subscription = None

    # noinspection PyUnusedLocal
    @tornado.gen.coroutine
    def render_get(self, request):
        """Returns a CoAP response with the last observed event emission."""

        payload = json.dumps(self._last_item).encode("utf-8") if self._last_item else b""
        response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=payload)
        response.opt.content_format = JSON_CONTENT_FORMAT

        raise tornado.gen.Return(response)
