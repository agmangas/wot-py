#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Property interactions.
"""

import tornado.gen
from tornado.concurrent import Future
from tornado.web import RequestHandler, HTTPError


def _get_exposed_thing(server, thing_name):
    """Utility function to retrieve an ExposedThing
    from the HTTPServer or raise an HTTPError."""

    try:
        return server.get_exposed_thing(thing_name)
    except ValueError:
        raise HTTPError(log_message="Unknown Thing: {}".format(thing_name))


# noinspection PyAbstractClass
class PropertyReadWriteHandler(RequestHandler):
    """Handler for Property get/set requests."""

    # noinspection PyMethodOverriding,PyAttributeOutsideInit
    def initialize(self, http_server):
        self._server = http_server

    @tornado.gen.coroutine
    def get(self, thing_name, name):
        """Reads and returns the Property value."""

        exposed_thing = _get_exposed_thing(self._server, thing_name)
        value = yield exposed_thing.properties[name].get()
        self.write({"value": value})

    @tornado.gen.coroutine
    def post(self, thing_name, name):
        """Updates the Property value."""

        exposed_thing = _get_exposed_thing(self._server, thing_name)
        value = self.get_argument("value")
        yield exposed_thing.properties[name].set(value)


# noinspection PyAbstractClass,PyAttributeOutsideInit
class PropertyObserverHandler(RequestHandler):
    """Handler for Property subscription requests."""

    # noinspection PyMethodOverriding
    def initialize(self, http_server):
        self._server = http_server

    @tornado.gen.coroutine
    def get(self, thing_name, name):
        """Subscribes to Property updates and waits for the next event (HTTP long-polling pattern).
        Returns the updated value and destroys the subscription."""

        exposed_thing = _get_exposed_thing(self._server, thing_name)

        future_next = Future()
        self.future_next = future_next

        def on_next(item):
            future_next.set_result(item.data.value)

        self.subscription = exposed_thing.properties[name].subscribe(on_next)
        updated_value = yield self.future_next
        self.write({"value": updated_value})

    def on_finish(self):
        """Destroys the subscription to the observable when the request finishes."""

        try:
            self.subscription.dispose()
        except AttributeError:
            pass
