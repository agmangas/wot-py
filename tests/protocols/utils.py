#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
from faker import Faker
from rx.concurrency import IOLoopScheduler

from wotpy.td.description import ThingDescription
from wotpy.wot.dictionaries.interaction import PropertyFragment


def client_test_on_property_change(servient, protocol_client_cls):
    """Helper function to test observation of Property updates on bindings clients."""

    exposed_thing = next(servient.exposed_things)

    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(prop_name, PropertyFragment({
        "type": "string",
        "writable": True,
        "observable": True
    }), value=Faker().sentence())

    servient.refresh_forms()

    td = ThingDescription.from_thing(exposed_thing.thing)

    @tornado.gen.coroutine
    def test_coroutine():
        protocol_client = protocol_client_cls()

        values = [Faker().sentence() for _ in range(10)]
        values_observed = {value: tornado.concurrent.Future() for value in values}

        @tornado.gen.coroutine
        def write_next():
            try:
                next_value = next(val for val, fut in six.iteritems(values_observed) if not fut.done())
                yield exposed_thing.properties[prop_name].write(next_value)
            except StopIteration:
                pass

        def on_next(ev):
            prop_value = ev.data.value
            if prop_value in values_observed and not values_observed[prop_value].done():
                values_observed[prop_value].set_result(True)

        observable = protocol_client.on_property_change(td, prop_name)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        periodic_emit = tornado.ioloop.PeriodicCallback(write_next, 10)
        periodic_emit.start()

        yield list(values_observed.values())

        periodic_emit.stop()
        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
