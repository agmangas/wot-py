#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Property interactions.
"""

import asyncio
import logging

from tornado.web import RequestHandler

import wotpy.protocols.http.handlers.utils as handler_utils


class PropertyReadWriteHandler(RequestHandler):
    """Handler for Property get/set requests."""

    def initialize(self, http_server):
        self._server = http_server

    async def get(self, thing_name, name):
        """Reads and returns the Property value."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        value = await exposed_thing.properties[name].read()
        self.write({"value": value})

    async def put(self, thing_name, name):
        """Updates the Property value."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        value = handler_utils.get_argument(self, "value", self.request.body)
        await exposed_thing.properties[name].write(value)


class PropertyObserverHandler(RequestHandler):
    """Handler for Property subscription requests."""

    def initialize(self, http_server):
        self._server = http_server
        self._logr = logging.getLogger(__name__)

    async def get(self, thing_name, name):
        """Subscribes to Property updates and waits for the next event (HTTP long-polling pattern).
        Returns the updated value and destroys the subscription."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        thing_property = exposed_thing.properties[name]

        future_next = asyncio.Future()

        def on_next(item):
            not future_next.done() and future_next.set_result(item.data.value)

        def on_error(err):
            self._logr.warning(
                "Error on subscription to {}: {}".format(thing_property, err)
            )
            not future_next.done() and future_next.set_exception(err)

        self.subscription = thing_property.subscribe(on_next=on_next, on_error=on_error)
        updated_value = await future_next
        self.write({"value": updated_value})

    def on_finish(self):
        """Destroys the subscription to the observable when the request finishes."""

        try:
            self.subscription.dispose()
        except AttributeError:
            pass
