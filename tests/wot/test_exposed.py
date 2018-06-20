#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
# noinspection PyCompatibility
from concurrent.futures import ThreadPoolExecutor

# noinspection PyPackageRequirements
import pytest
import six
import tornado.gen
import tornado.ioloop
# noinspection PyPackageRequirements
from faker import Faker
from tornado.concurrent import Future

from wotpy.wot.dictionaries import PropertyInitDict
from wotpy.wot.enums import TDChangeMethod, TDChangeType


def test_read_property(exposed_thing, property_init):
    """Properties may be retrieved on ExposedThings."""

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_init)
        value = yield exposed_thing.read_property(prop_name)
        assert value == property_init.value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_write_property(exposed_thing, property_init):
    """Properties may be updated on ExposedThings."""

    assert property_init.writable

    @tornado.gen.coroutine
    def test_coroutine():
        updated_val = Faker().pystr()
        prop_name = Faker().pystr()

        exposed_thing.add_property(prop_name, property_init)

        yield exposed_thing.write_property(prop_name, updated_val)

        value = yield exposed_thing.read_property(prop_name)

        assert value == updated_val

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_write_non_writable_property(exposed_thing):
    """Attempts to write a non-writable property should return an error."""

    prop_init_non_writable = PropertyInitDict({
        "type": "string",
        "writable": False
    })

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, prop_init_non_writable)

        with pytest.raises(Exception):
            yield exposed_thing.write_property(prop_name, Faker().pystr())

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_invoke_action(exposed_thing, action_init):
    """Actions can be invoked on ExposedThings."""

    thread_executor = ThreadPoolExecutor(max_workers=1)

    def upper_thread(parameters):
        input_value = parameters.get("input")
        return thread_executor.submit(lambda x: time.sleep(0.1) or str(x).upper(), input_value)

    def upper(parameters):
        loop = tornado.ioloop.IOLoop.current()
        input_value = parameters.get("input")
        return loop.run_in_executor(None, lambda x: time.sleep(0.1) or str(x).upper(), input_value)

    @tornado.gen.coroutine
    def lower(parameters):
        input_value = parameters.get("input")
        yield tornado.gen.sleep(0.1)
        raise tornado.gen.Return(str(input_value).lower())

    def title(parameters):
        input_value = parameters.get("input")
        future = Future()
        future.set_result(input_value.title())
        return future

    handlers_map = {
        upper_thread: lambda x: x.upper(),
        upper: lambda x: x.upper(),
        lower: lambda x: x.lower(),
        title: lambda x: x.title()
    }

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = Faker().pystr()
        exposed_thing.add_action(action_name, action_init)

        for handler, assert_func in six.iteritems(handlers_map):
            exposed_thing.set_action_handler(action_name, handler)
            action_arg = Faker().sentence(10)
            result = yield exposed_thing.invoke_action(action_name, action_arg)
            assert result == assert_func(action_arg)

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_invoke_action_undefined_handler(exposed_thing, action_init):
    """Actions with undefined handlers return an error."""

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = Faker().pystr()
        exposed_thing.add_action(action_name, action_init)

        with pytest.raises(NotImplementedError):
            yield exposed_thing.invoke_action(action_name)

        @tornado.gen.coroutine
        def dummy_func(parameters):
            assert parameters.get("input") is None
            raise tornado.gen.Return(True)

        exposed_thing.set_action_handler(action_name, dummy_func)

        result = yield exposed_thing.invoke_action(action_name)

        assert result

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_on_property_change(exposed_thing, property_init):
    """Property changes can be observed."""

    assert property_init.observable

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_init)

        observable_prop = exposed_thing.on_property_change(prop_name)

        property_values = Faker().pylist(5, True, *(str,))

        emitted_values = []

        def on_next_property_event(ev):
            emitted_values.append(ev.data.value)

        subscription = observable_prop.subscribe(on_next_property_event)

        for val in property_values:
            yield exposed_thing.write_property(prop_name, val)

        assert emitted_values == property_values

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_on_property_change_non_observable(exposed_thing, property_init):
    """Observe requests to non-observable properties are rejected."""

    prop_init_non_observable = PropertyInitDict({
        "type": "string",
        "writable": True,
        "observable": False
    })

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, prop_init_non_observable)

        observable_prop = exposed_thing.on_property_change(prop_name)

        future_next = Future()
        future_error = Future()

        def on_next(item):
            future_next.set_result(item)

        def on_error(err):
            future_error.set_exception(err)

        subscription = observable_prop.subscribe(on_next=on_next, on_error=on_error)

        yield exposed_thing.write_property(prop_name, Faker().pystr())

        with pytest.raises(Exception):
            future_error.result()

        assert not future_next.done()

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_on_event(exposed_thing, event_init):
    """Events defined in the Thing Description can be observed."""

    event_name = Faker().pystr()
    exposed_thing.add_event(event_name, event_init)

    observable_event = exposed_thing.on_event(event_name)

    event_payloads = [Faker().pystr() for _ in range(5)]

    emitted_payloads = []

    def on_next_event(ev):
        emitted_payloads.append(ev.data)

    subscription = observable_event.subscribe(on_next_event)

    for val in event_payloads:
        exposed_thing.emit_event(event_name, val)

    assert emitted_payloads == event_payloads

    subscription.dispose()


def _test_td_change_events(exposed_thing, property_init, event_init, action_init, subscribe_func):
    """Helper function to test subscriptions to TD changes."""

    prop_name = Faker().pystr()
    event_name = Faker().pystr()
    action_name = Faker().pystr()

    complete_futures = {
        (TDChangeType.PROPERTY, TDChangeMethod.ADD): Future(),
        (TDChangeType.PROPERTY, TDChangeMethod.REMOVE): Future(),
        (TDChangeType.EVENT, TDChangeMethod.ADD): Future(),
        (TDChangeType.EVENT, TDChangeMethod.REMOVE): Future(),
        (TDChangeType.ACTION, TDChangeMethod.ADD): Future(),
        (TDChangeType.ACTION, TDChangeMethod.REMOVE): Future()
    }

    def on_next(ev):
        change_type = ev.data.td_change_type
        change_method = ev.data.method
        interaction_name = ev.data.name
        future_key = (change_type, change_method)
        complete_futures[future_key].set_result(interaction_name)

    subscription = subscribe_func(on_next)

    exposed_thing.add_event(event_name, event_init)

    assert complete_futures[(TDChangeType.EVENT, TDChangeMethod.ADD)].result() == event_name
    assert not complete_futures[(TDChangeType.EVENT, TDChangeMethod.REMOVE)].done()

    exposed_thing.remove_event(name=event_name)
    exposed_thing.add_property(prop_name, property_init)

    assert complete_futures[(TDChangeType.EVENT, TDChangeMethod.REMOVE)].result() == event_name
    assert complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.ADD)].result() == prop_name
    assert not complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.REMOVE)].done()

    exposed_thing.remove_property(name=prop_name)
    exposed_thing.add_action(action_name, action_init)
    exposed_thing.remove_action(name=action_name)

    assert complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.REMOVE)].result() == prop_name
    assert complete_futures[(TDChangeType.ACTION, TDChangeMethod.ADD)].result() == action_name
    assert complete_futures[(TDChangeType.ACTION, TDChangeMethod.REMOVE)].result() == action_name

    subscription.dispose()


def test_on_td_change(exposed_thing, property_init, event_init, action_init):
    """Thing Description changes can be observed."""

    def subscribe_func(*args, **kwargs):
        return exposed_thing.on_td_change().subscribe(*args, **kwargs)

    _test_td_change_events(exposed_thing, property_init, event_init, action_init, subscribe_func)


def test_thing_property_get(exposed_thing, property_init):
    """Property values can be retrieved on ExposedThings using the map-like interface."""

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_init)
        value = yield exposed_thing.properties[prop_name].get()
        assert value == property_init.value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_thing_property_set(exposed_thing, property_init):
    """Property values can be updated on ExposedThings using the map-like interface."""

    assert property_init.writable

    @tornado.gen.coroutine
    def test_coroutine():
        updated_val = Faker().pystr()
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_init)
        yield exposed_thing.properties[prop_name].set(updated_val)
        value = yield exposed_thing.properties[prop_name].get()
        assert value == updated_val

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_thing_property_subscribe(exposed_thing, property_init):
    """Property updates can be observed on ExposedThings using the map-like interface."""

    assert property_init.observable

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_init)

        property_values = [Faker().sentence() for _ in range(10)]

        emitted_values = []

        def on_next(ev):
            emitted_values.append(ev.data.value)

        subscription = exposed_thing.properties[prop_name].subscribe(on_next)

        for val in property_values:
            yield exposed_thing.properties[prop_name].set(val)

        assert emitted_values == property_values

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_thing_property_getters(exposed_thing, property_init):
    """Property init attributes can be accessed using the map-like interface."""

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_init)
        thing_property = exposed_thing.properties[prop_name]

        assert thing_property.label == property_init.label
        assert thing_property.value == property_init.value
        assert thing_property.writable == property_init.writable
        assert thing_property.observable == property_init.observable
        assert thing_property.type == property_init.type

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_thing_action_run(exposed_thing, action_init):
    """Actions can be invoked on ExposedThings using the map-like interface."""

    @tornado.gen.coroutine
    def lower(parameters):
        input_value = parameters.get("input")
        raise tornado.gen.Return(str(input_value).lower())

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = Faker().pystr()
        exposed_thing.add_action(action_name, action_init)
        exposed_thing.set_action_handler(action_name, lower)
        input_value = Faker().pystr()

        result = yield exposed_thing.actions[action_name].run(input_value)
        result_expected = yield exposed_thing.invoke_action(action_name, input_value)

        assert result == result_expected

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_thing_action_getters(exposed_thing, action_init):
    """Action init attributes can be accessed using the map-like interface."""

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = Faker().pystr()
        exposed_thing.add_action(action_name, action_init)
        thing_action = exposed_thing.actions[action_name]

        assert thing_action.label == action_init.label
        assert thing_action.description == action_init.description
        assert thing_action.input.type == action_init.input.type
        assert thing_action.output.type == action_init.output.type

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_thing_event_subscribe(exposed_thing, event_init):
    """Property updates can be observed on ExposedThings using the map-like interface."""

    @tornado.gen.coroutine
    def test_coroutine():
        event_name = Faker().pystr()
        exposed_thing.add_event(event_name, event_init)

        event_values = [Faker().sentence() for _ in range(10)]

        emitted_values = []

        def on_next(ev):
            emitted_values.append(ev.data)

        subscription = exposed_thing.events[event_name].subscribe(on_next)

        for val in event_values:
            yield exposed_thing.emit_event(event_name, val)

        assert emitted_values == event_values

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_thing_event_getters(exposed_thing, event_init):
    """Event init attributes can be accessed using the map-like interface."""

    @tornado.gen.coroutine
    def test_coroutine():
        event_name = Faker().pystr()
        exposed_thing.add_event(event_name, event_init)
        thing_event = exposed_thing.events[event_name]

        assert thing_event.label == event_init.label
        assert thing_event.type == event_init.type

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_set_property_read_handler(exposed_thing, property_init):
    """Read handlers can be defined for ExposedThing property interactions."""

    const_prop_value = Faker().sentence()

    @tornado.gen.coroutine
    def read_handler():
        raise tornado.gen.Return(const_prop_value)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_init)
        exposed_thing.set_property_read_handler(prop_name, read_handler)
        value = yield exposed_thing.properties[prop_name].get()
        assert value == const_prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_set_property_write_handler(exposed_thing, property_init):
    """Write handlers can be defined for ExposedThing property interactions."""

    prop_history = []

    @tornado.gen.coroutine
    def write_handler(value):
        yield tornado.gen.sleep(0.01)
        prop_history.append(value)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_init)
        exposed_thing.set_property_write_handler(prop_name, write_handler)
        prop_value = Faker().sentence()
        assert not len(prop_history)
        yield exposed_thing.properties[prop_name].set(prop_value)
        assert prop_value in prop_history

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_subscribe(exposed_thing, property_init, event_init, action_init):
    """Subscribing to the ExposedThing provides Thing Description update events."""

    def subscribe_func(*args, **kwargs):
        return exposed_thing.subscribe(*args, **kwargs)

    _test_td_change_events(exposed_thing, property_init, event_init, action_init, subscribe_func)
