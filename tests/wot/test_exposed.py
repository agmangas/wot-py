#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
import tornado.testing
# noinspection PyCompatibility
from concurrent.futures import Future
from faker import Faker
from tornado import ioloop

from tests.utils import FutureTimeout
from tests.wot.utils import build_exposed_thing, build_thing_property_init
from wotpy.wot.enums import RequestType


def test_get_property():
    """Properties may be retrieved on ExposedThings."""

    exp_thing = build_exposed_thing()
    prop_init = build_thing_property_init()

    exp_thing.add_property(property_init=prop_init)
    future_get = exp_thing.get_property(prop_init.name)

    assert future_get.result(timeout=FutureTimeout.MINIMAL) == prop_init.value


def test_set_property():
    """Properties may be updated on ExposedThings."""

    fake = Faker()

    exp_thing = build_exposed_thing()
    prop_init = build_thing_property_init()

    prop_init.writable = True
    exp_thing.add_property(property_init=prop_init)
    updated_val = fake.pystr()
    future_set = exp_thing.set_property(prop_init.name, updated_val)
    future_set.result(timeout=FutureTimeout.MINIMAL)
    future_get = exp_thing.get_property(prop_init.name)

    assert future_get.result(timeout=FutureTimeout.MINIMAL) == updated_val


def test_on_retrieve_property():
    """Custom handlers to retrieve properties can be defined on ExposedThings."""

    fake = Faker()

    exp_thing = build_exposed_thing()
    prop_init = build_thing_property_init()

    dummy_value = fake.pystr()

    def _handler_dummy(request):
        request.respond(dummy_value)

    def _handler_error(request):
        request.respond_with_error(ValueError())

    exp_thing.add_property(property_init=prop_init)
    exp_thing.on_retrieve_property(_handler_dummy)
    future_get_01 = exp_thing.get_property(prop_init.name)

    assert future_get_01.result(timeout=FutureTimeout.MINIMAL) == dummy_value

    future_set = exp_thing.set_property(prop_init.name, fake.pystr())
    future_set.result(timeout=FutureTimeout.MINIMAL)
    future_get_02 = exp_thing.get_property(prop_init.name)

    assert future_get_02.result(timeout=FutureTimeout.MINIMAL) == dummy_value

    exp_thing.on_retrieve_property(_handler_error)
    future_get_03 = exp_thing.get_property(prop_init.name)

    with pytest.raises(ValueError):
        future_get_03.result(timeout=FutureTimeout.MINIMAL)


class TestObservePropertyChange(tornado.testing.AsyncTestCase):
    """Test case for property updates observation."""

    @tornado.testing.gen_test
    def test_observe_property_change(self):
        """Property changes can be observed."""

        fake = Faker()

        exp_thing = build_exposed_thing()
        prop_init = build_thing_property_init()

        exp_thing.add_property(property_init=prop_init)

        observable = exp_thing.observe(
            name=prop_init.name, request_type=RequestType.PROPERTY)

        values = fake.pylist(5, True, *(int,))
        event_complete_futures = dict((val, Future()) for val in values)

        ready_future = Future()

        def _on_next(ev):
            ready_future.set_result(True)
            if event_complete_futures.get(ev.data.value):
                event_complete_futures[ev.data.value].set_result(True)

        subscription = observable.subscribe(_on_next)

        def _set_dummy():
            exp_thing.set_property(prop_init.name, None)

        periodic_cb = ioloop.PeriodicCallback(callback=_set_dummy, callback_time=50)
        periodic_cb.start()

        yield ready_future

        periodic_cb.stop()

        for val in values:
            yield exp_thing.set_property(prop_init.name, val)

        yield event_complete_futures

        subscription.dispose()
