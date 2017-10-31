#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

# noinspection PyPackageRequirements
import pytest
# noinspection PyCompatibility
from concurrent.futures import Future, ThreadPoolExecutor
# noinspection PyPackageRequirements
from faker import Faker

from tests.utils import FutureTimeout
from wotpy.wot.enums import RequestType, TDChangeMethod, TDChangeType
# noinspection PyUnresolvedReferences
from tests.wot.fixtures import \
    exposed_thing, \
    thing_property_init, \
    thing_event_init, \
    thing_action_init


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
    """A custom global handler to retrieve properties can be defined on a ExposedThing."""

    fake = Faker()

    dummy_value = fake.pystr()

    def _handler_dummy(request):
        request.respond(dummy_value)

    def _handler_error(request):
        request.respond_with_error(ValueError())

    exposed_thing.add_property(property_init=thing_property_init)
    exposed_thing.on_retrieve_property(_handler_dummy)

    assert exposed_thing.get_property(thing_property_init.name).result() == dummy_value

    future_set = exposed_thing.set_property(thing_property_init.name, fake.pystr())

    assert future_set.done()
    assert exposed_thing.get_property(thing_property_init.name).result() == dummy_value

    exposed_thing.on_retrieve_property(_handler_error)

    with pytest.raises(ValueError):
        exposed_thing.get_property(thing_property_init.name).result()


def test_on_retrieve_specific_property(exposed_thing, thing_property_init):
    """Custom handlers to retrieve specific properties can be defined on a ExposedThing."""

    fake = Faker()

    prop_init_01 = copy.deepcopy(thing_property_init)
    prop_init_02 = copy.deepcopy(thing_property_init)

    prop_init_01.name = fake.pystr()
    prop_init_01.value = fake.pystr()

    prop_init_02.name = fake.pystr()
    prop_init_02.value = fake.pystr()

    dummy_value = fake.pystr()

    def _handler_dummy(request):
        request.respond(dummy_value)

    exposed_thing.add_property(property_init=prop_init_01)
    exposed_thing.add_property(property_init=prop_init_02)
    exposed_thing.on_retrieve_property(handler=_handler_dummy, name=prop_init_01.name)

    assert exposed_thing.get_property(prop_init_01.name).result() == dummy_value
    assert exposed_thing.get_property(prop_init_01.name).result() != prop_init_01.value
    assert exposed_thing.get_property(prop_init_02.name).result() == prop_init_02.value

    future_set = exposed_thing.set_property(prop_init_01.name, fake.pystr())

    assert future_set.done()
    assert exposed_thing.get_property(prop_init_01.name).result() == dummy_value


# noinspection PyShadowingNames
def test_invoke_action_sync(exposed_thing, thing_action_init):
    """Synchronous actions can be invoked on ExposedThings."""

    fake = Faker()
    action_arg = fake.pystr()

    def _upper(val):
        return str(val).upper()

    thing_action_init.action = _upper

    exposed_thing.add_action(action_init=thing_action_init)
    future_result = exposed_thing.invoke_action(thing_action_init.name, val=action_arg)

    assert future_result.result(timeout=FutureTimeout.MINIMAL) == action_arg.upper()


# noinspection PyShadowingNames
def test_invoke_action_async(exposed_thing, thing_action_init):
    """Asynchronous actions can be invoked on ExposedThings."""

    fake = Faker()
    action_arg = fake.pystr()

    executor = ThreadPoolExecutor(max_workers=1)

    def _upper(val):
        return str(val).upper()

    def _async_upper(val):
        return executor.submit(_upper, val)

    thing_action_init.action = _async_upper

    exposed_thing.add_action(action_init=thing_action_init)
    future_result = exposed_thing.invoke_action(thing_action_init.name, val=action_arg)

    assert future_result.result(timeout=FutureTimeout.MINIMAL) == action_arg.upper()


# noinspection PyShadowingNames
def test_observe_property_change(exposed_thing, thing_property_init):
    """Property changes can be observed."""

    fake = Faker()

    prop_name = thing_property_init.name
    exposed_thing.add_property(property_init=thing_property_init)

    observable = exposed_thing.observe(
        name=prop_name,
        request_type=RequestType.PROPERTY)

    property_values = fake.pylist(5, True, *(str,))

    emitted_values = []

    def _on_next(ev):
        emitted_values.append(ev.data.value)

    subscription = observable.subscribe(_on_next)

    for val in property_values:
        future_set = exposed_thing.set_property(prop_name, val)
        future_set.result(timeout=FutureTimeout.MINIMAL)

    assert emitted_values == property_values

    subscription.dispose()


# noinspection PyShadowingNames
def test_observe_event(exposed_thing, thing_event_init):
    """Events defined in the Thing Description can be observed."""

    fake = Faker()

    event_name = thing_event_init.name
    exposed_thing.add_event(event_init=thing_event_init)

    observable = exposed_thing.observe(
        name=event_name,
        request_type=RequestType.EVENT)

    event_payloads = fake.pylist(5, True, *(str,))

    emitted_payloads = []

    def _on_next(ev):
        emitted_payloads.append(ev.data)

    subscription = observable.subscribe(_on_next)

    for val in event_payloads:
        exposed_thing.emit_event(event_name, val)

    assert emitted_payloads == event_payloads

    subscription.dispose()


# noinspection PyShadowingNames
def test_observe_invoke_action(exposed_thing, thing_action_init):
    """Events defined in the Thing Description can be observed."""

    fake = Faker()

    executor = ThreadPoolExecutor(max_workers=1)

    def _async_lower(val):
        return executor.submit(lambda x: x.lower(), val)

    thing_action_init.action = _async_lower

    exposed_thing.add_action(action_init=thing_action_init)

    observable = exposed_thing.observe(
        name=thing_action_init.name,
        request_type=RequestType.ACTION)

    future_event_emitted = Future()

    def _on_next(ev):
        future_event_emitted.set_result(ev.data.action_name)

    subscription = observable.subscribe(_on_next)

    action_arg = fake.pystr()
    future_result = exposed_thing.invoke_action(thing_action_init.name, val=action_arg)

    assert future_result.result(timeout=FutureTimeout.MINIMAL) == action_arg.lower()
    assert future_event_emitted.result(timeout=FutureTimeout.MINIMAL) == thing_action_init.name

    subscription.dispose()


# noinspection PyShadowingNames
def test_observe_td_changes(exposed_thing, thing_property_init, thing_event_init, thing_action_init):
    """Thing Description changes can be observed."""

    prop_name = thing_property_init.name
    event_name = thing_event_init.name
    action_name = thing_action_init.name

    observable = exposed_thing.observe(request_type=RequestType.TD)

    complete_futures = {
        (TDChangeType.PROPERTY, TDChangeMethod.ADD): Future(),
        (TDChangeType.PROPERTY, TDChangeMethod.REMOVE): Future(),
        (TDChangeType.EVENT, TDChangeMethod.ADD): Future(),
        (TDChangeType.EVENT, TDChangeMethod.REMOVE): Future(),
        (TDChangeType.ACTION, TDChangeMethod.ADD): Future(),
        (TDChangeType.ACTION, TDChangeMethod.REMOVE): Future()
    }

    def _on_next(ev):
        change_type = ev.data.td_change_type
        change_method = ev.data.method
        interaction_name = ev.data.name
        future_key = (change_type, change_method)
        complete_futures[future_key].set_result(interaction_name)

    subscription = observable.subscribe(_on_next)

    exposed_thing.add_event(event_init=thing_event_init)

    assert complete_futures[(TDChangeType.EVENT, TDChangeMethod.ADD)].result() == event_name
    assert not complete_futures[(TDChangeType.EVENT, TDChangeMethod.REMOVE)].done()

    exposed_thing.remove_event(name=event_name)
    exposed_thing.add_property(property_init=thing_property_init)

    assert complete_futures[(TDChangeType.EVENT, TDChangeMethod.REMOVE)].result() == event_name
    assert complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.ADD)].result() == prop_name
    assert not complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.REMOVE)].done()

    exposed_thing.remove_property(name=prop_name)
    exposed_thing.add_action(action_init=thing_action_init)
    exposed_thing.remove_action(name=action_name)

    assert complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.REMOVE)].result() == prop_name
    assert complete_futures[(TDChangeType.ACTION, TDChangeMethod.ADD)].result() == action_name
    assert complete_futures[(TDChangeType.ACTION, TDChangeMethod.REMOVE)].result() == action_name

    subscription.dispose()
