#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

# noinspection PyPackageRequirements
import pytest
import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.websocket
from rx.concurrency import IOLoopScheduler
from tornado.concurrent import Future

from wotpy.protocols.http.client import HTTPClient
from wotpy.td.description import ThingDescription


@pytest.mark.flaky(reruns=5)
def test_on_event(http_servient):
    """The HTTP client can observe events."""

    exposed_thing = next(http_servient.exposed_things)
    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = HTTPClient()

        event_name = next(six.iterkeys(td.events))

        observable = http_client.on_event(td, event_name)

        payloads = [uuid.uuid4().hex for _ in range(10)]
        future_payloads = {key: Future() for key in payloads}

        @tornado.gen.coroutine
        def emit_next_event():
            next_value = next(val for val, fut in six.iteritems(future_payloads) if not fut.done())
            exposed_thing.events[event_name].emit(next_value)

        def on_next(ev):
            if ev.data in future_payloads and not future_payloads[ev.data].done():
                future_payloads[ev.data].set_result(True)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        periodic_emit = tornado.ioloop.PeriodicCallback(emit_next_event, 10)
        periodic_emit.start()

        yield list(future_payloads.values())

        periodic_emit.stop()
        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
