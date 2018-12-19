#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Request handler for Event interactions.
"""

import logging

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
        self._logr = logging.getLogger(__name__)

    @tornado.gen.coroutine
    def get(self, thing_name, name):
        """Subscribes to the given Event and waits for the next emission (HTTP long-polling pattern).
        Returns the event emission payload and destroys the subscription afterwards."""

        exposed_thing = handler_utils.get_exposed_thing(self._server, thing_name)
        thing_event = exposed_thing.events[name]

        future_next = Future()

        def on_next(item):
            not future_next.done() and future_next.set_result(item.data)

        def on_error(err):
            self._logr.warning("Error on subscription to {}: {}".format(thing_event, err))
            not future_next.done() and future_next.set_exception(err)

        self.subscription = thing_event.subscribe(on_next=on_next, on_error=on_error)
        event_payload = yield future_next
        self.write({"payload": event_payload})

    def on_finish(self):
        """Destroys the subscription to the observable when the request finishes."""

        try:
            self.subscription.dispose()
        except AttributeError:
            pass
