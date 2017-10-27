#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import tornado.testing
# noinspection PyCompatibility
from concurrent.futures import Future
from faker import Faker
from tornado import ioloop, gen

from tests.utils import FutureTimeout
from tests.wot.fixtures import exposed_thing, thing_property_init, thing_event_init
from wotpy.wot.enums import RequestType


# noinspection PyShadowingNames
def test_get_property(exposed_thing, thing_property_init):
    """Properties may be retrieved on ExposedThings."""

    exposed_thing.add_property(property_init=thing_property_init)
    future_get = exposed_thing.get_property(thing_property_init.name)

    assert future_get.result(timeout=FutureTimeout.MINIMAL) == thing_property_init.value


# noinspection PyShadowingNames
def test_set_property(exposed_thing, thing_property_init):
    """Properties may be updated on ExposedThings."""

    fake = Faker()

    thing_property_init.writable = True
    exposed_thing.add_property(property_init=thing_property_init)
    updated_val = fake.pystr()
    future_set = exposed_thing.set_property(thing_property_init.name, updated_val)
    future_set.result(timeout=FutureTimeout.MINIMAL)
    future_get = exposed_thing.get_property(thing_property_init.name)

    assert future_get.result(timeout=FutureTimeout.MINIMAL) == updated_val


# noinspection PyShadowingNames
def test_on_retrieve_property(exposed_thing, thing_property_init):
    """Custom handlers to retrieve properties can be defined on ExposedThings."""

    fake = Faker()

    dummy_value = fake.pystr()

    def _handler_dummy(request):
        request.respond(dummy_value)

    def _handler_error(request):
        request.respond_with_error(ValueError())

    exposed_thing.add_property(property_init=thing_property_init)
    exposed_thing.on_retrieve_property(_handler_dummy)
    future_get_01 = exposed_thing.get_property(thing_property_init.name)

    assert future_get_01.result(timeout=FutureTimeout.MINIMAL) == dummy_value

    future_set = exposed_thing.set_property(thing_property_init.name, fake.pystr())
    future_set.result(timeout=FutureTimeout.MINIMAL)
    future_get_02 = exposed_thing.get_property(thing_property_init.name)

    assert future_get_02.result(timeout=FutureTimeout.MINIMAL) == dummy_value

    exposed_thing.on_retrieve_property(_handler_error)
    future_get_03 = exposed_thing.get_property(thing_property_init.name)

    with pytest.raises(ValueError):
        future_get_03.result(timeout=FutureTimeout.MINIMAL)


class TestObserve(tornado.testing.AsyncTestCase):
    """Test case for observation requests."""

    def setUp(self):
        super(TestObserve, self).setUp()
        self.exposed_thing = exposed_thing()
        self.thing_property_init = thing_property_init()
        self.thing_event_init = thing_event_init()
        self.exposed_thing.add_property(property_init=self.thing_property_init)
        self.exposed_thing.add_event(event_init=self.thing_event_init)
        self.periodic_cb = None
        self.subscription = None
        self.fake = Faker()

    def tearDown(self):
        if self.periodic_cb:
            self.periodic_cb.stop()

        if self.subscription:
            self.subscription.dispose()

    @tornado.testing.gen_test
    def test_observe_property_change(self):
        """Property changes can be observed."""

        prop_name = self.thing_property_init.name

        observable = self.exposed_thing.observe(
            name=prop_name,
            request_type=RequestType.PROPERTY)

        values = self.fake.pylist(5, True, *(str,))
        event_complete_futures = dict((val, Future()) for val in values)

        def _on_next(ev):
            emitted_value = ev.data.value
            if event_complete_futures.get(emitted_value):
                event_complete_futures[emitted_value].set_result(True)

        self.subscription = observable.subscribe(_on_next)

        @gen.coroutine
        def _set_properties():
            for val in values:
                yield self.exposed_thing.set_property(prop_name, val)

        self.periodic_cb = ioloop.PeriodicCallback(callback=_set_properties, callback_time=50)
        self.periodic_cb.start()

        yield event_complete_futures

    @tornado.testing.gen_test
    def test_observe_event(self):
        """TD-defined events can be observed."""

        event_name = self.thing_event_init.name

        observable = self.exposed_thing.observe(
            name=event_name,
            request_type=RequestType.EVENT)

        values = self.fake.pylist(5, True, *(str,))
        event_complete_futures = dict((val, Future()) for val in values)

        def _on_next(ev):
            emitted_value = ev.data
            if event_complete_futures.get(emitted_value):
                event_complete_futures[emitted_value].set_result(True)

        self.subscription = observable.subscribe(_on_next)

        @gen.coroutine
        def _emit_events():
            for val in values:
                yield self.exposed_thing.emit_event(event_name, val)

        self.periodic_cb = ioloop.PeriodicCallback(callback=_emit_events, callback_time=50)
        self.periodic_cb.start()

        yield event_complete_futures
