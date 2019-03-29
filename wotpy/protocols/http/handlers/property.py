#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Property interactions.
"""

import logging

import tornado.gen
from tornado.concurrent import Future
from tornado.web import RequestHandler

import wotpy.protocols.http.handlers.utils as handler_utils


# noinspection PyAbstractClass
class PropertyReadWriteHandler(RequestHandler):
    """Handler for Property get/set requests."""

    # noinspection PyMethodOverriding,PyAttributeOutsideInit
    def initialize(self, http_server):
        self._server = http_server

    @tornado.gen.coroutine
    def get(self, thing_name, name):
        """Reads and returns the Property value."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        value = yield exposed_thing.properties[name].read()
        self.write({"value": value})

    @tornado.gen.coroutine
    def put(self, thing_name, name):
        """Updates the Property value."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        value = handler_utils.get_argument(self, "value")
        yield exposed_thing.properties[name].write(value)


# noinspection PyAbstractClass,PyAttributeOutsideInit
class PropertyObserverHandler(RequestHandler):
    """Handler for Property subscription requests."""

    # noinspection PyMethodOverriding
    def initialize(self, http_server):
        self._server = http_server
        self._logr = logging.getLogger(__name__)

    @tornado.gen.coroutine
    def get(self, thing_name, name):
        """Subscribes to Property updates and waits for the next event (HTTP long-polling pattern).
        Returns the updated value and destroys the subscription."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        thing_property = exposed_thing.properties[name]

        future_next = Future()

        def on_next(item):
            not future_next.done() and future_next.set_result(item.data.value)

        def on_error(err):
            self._logr.warning("Error on subscription to {}: {}".format(thing_property, err))
            not future_next.done() and future_next.set_exception(err)

        self.subscription = thing_property.subscribe(on_next=on_next, on_error=on_error)
        updated_value = yield future_next
        self.write({"value": updated_value})

    def on_finish(self):
        """Destroys the subscription to the observable when the request finishes."""

        try:
            self.subscription.dispose()
        except AttributeError:
            pass
