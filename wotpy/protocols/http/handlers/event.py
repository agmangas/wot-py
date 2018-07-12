#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Event interactions.
"""

import tornado.gen
from tornado.concurrent import Future
from tornado.web import RequestHandler

import wotpy.protocols.http.handlers.utils as handler_utils


# noinspection PyAbstractClass,PyAttributeOutsideInit
class EventObserverHandler(RequestHandler):
    """Handler for Event subscription requests."""

    # noinspection PyMethodOverriding
    def initialize(self, http_server):
        self._server = http_server

    @tornado.gen.coroutine
    def get(self, thing_name, name):
        """Subscribes to the given Event and waits for the next emission (HTTP long-polling pattern).
        Returns the event emission payload and destroys the subscription afterwards."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)

        future_next = Future()
        self.future_next = future_next

        def on_next(item):
            future_next.set_result(item.data)

        self.subscription = exposed_thing.events[name].subscribe(on_next)
        event_payload = yield self.future_next
        self.write({"payload": event_payload})

    def on_finish(self):
        """Destroys the subscription to the observable when the request finishes."""

        try:
            self.subscription.dispose()
        except AttributeError:
            pass
