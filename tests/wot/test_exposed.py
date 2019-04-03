#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import uuid
# noinspection PyCompatibility
from concurrent.futures import ThreadPoolExecutor

import pytest
import six
import tornado.gen
import tornado.ioloop
from faker import Faker
from slugify import slugify
from tornado.concurrent import Future

from tests.utils import run_test_coroutine
from wotpy.wot.dictionaries.interaction import PropertyFragmentDict
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.enums import TDChangeMethod, TDChangeType, DataType
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.thing import Thing


def _test_td_change_events(exposed_thing, property_fragment, event_fragment, action_fragment, subscribe_func):
    """Helper function to test subscriptions to TD changes."""

    @tornado.gen.coroutine
    def test_coroutine():
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

        yield tornado.gen.sleep(0)

        exposed_thing.add_event(event_name, event_fragment)

        assert complete_futures[(TDChangeType.EVENT, TDChangeMethod.ADD)].result() == event_name
        assert not complete_futures[(TDChangeType.EVENT, TDChangeMethod.REMOVE)].done()

        exposed_thing.remove_event(name=event_name)
        exposed_thing.add_property(prop_name, property_fragment)

        assert complete_futures[(TDChangeType.EVENT, TDChangeMethod.REMOVE)].result() == event_name
        assert complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.ADD)].result() == prop_name
        assert not complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.REMOVE)].done()

        exposed_thing.remove_property(name=prop_name)
        exposed_thing.add_action(action_name, action_fragment)
        exposed_thing.remove_action(name=action_name)

        assert complete_futures[(TDChangeType.PROPERTY, TDChangeMethod.REMOVE)].result() == prop_name
        assert complete_futures[(TDChangeType.ACTION, TDChangeMethod.ADD)].result() == action_name
        assert complete_futures[(TDChangeType.ACTION, TDChangeMethod.REMOVE)].result() == action_name

        subscription.dispose()

    run_test_coroutine(test_coroutine)


def test_thing_template_getters(exposed_thing):
    """ThingTemplate properties can be accessed from the ExposedThing."""

    thing_template = exposed_thing.thing.thing_fragment

    assert exposed_thing.id == thing_template.id
    assert exposed_thing.name == thing_template.name
    assert exposed_thing.description == thing_template.description


def test_read_property(exposed_thing, property_fragment):
    """Properties may be retrieved on ExposedThings."""

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        prop_init_value = Faker().sentence()
        exposed_thing.add_property(prop_name, property_fragment, value=prop_init_value)
        value = yield exposed_thing.read_property(prop_name)
        assert value == prop_init_value

    run_test_coroutine(test_coroutine)


def test_write_property(exposed_thing, property_fragment):
    """Properties may be updated on ExposedThings."""

    assert property_fragment.writable

    @tornado.gen.coroutine
    def test_coroutine():
        updated_val = Faker().pystr()
        prop_name = Faker().pystr()

        exposed_thing.add_property(prop_name, property_fragment)

        yield exposed_thing.write_property(prop_name, updated_val)

        value = yield exposed_thing.read_property(prop_name)

        assert value == updated_val

    run_test_coroutine(test_coroutine)


def test_write_non_writable_property(exposed_thing):
    """Attempts to write a non-writable property should return an error."""

    prop_init_non_writable = PropertyFragmentDict({
        "type": "string",
        "readOnly": True
    })

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, prop_init_non_writable)

        with pytest.raises(Exception):
            yield exposed_thing.write_property(prop_name, Faker().pystr())

    run_test_coroutine(test_coroutine)


def test_invoke_action(exposed_thing, action_fragment):
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
        yield tornado.gen.sleep(0)
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
        exposed_thing.add_action(action_name, action_fragment)

        for handler, assert_func in six.iteritems(handlers_map):
            exposed_thing.set_action_handler(action_name, handler)
            action_arg = Faker().sentence(10)
            result = yield exposed_thing.invoke_action(action_name, action_arg)
            assert result == assert_func(action_arg)

    run_test_coroutine(test_coroutine)


def test_invoke_action_undefined_handler(exposed_thing, action_fragment):
    """Actions with undefined handlers return an error."""

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = Faker().pystr()
        exposed_thing.add_action(action_name, action_fragment)

        with pytest.raises(NotImplementedError):
            yield exposed_thing.invoke_action(action_name)

        @tornado.gen.coroutine
        def dummy_func(parameters):
            assert parameters.get("input") is None
            raise tornado.gen.Return(True)

        exposed_thing.set_action_handler(action_name, dummy_func)

        result = yield exposed_thing.invoke_action(action_name)

        assert result

    run_test_coroutine(test_coroutine)


def test_on_property_change(exposed_thing, property_fragment):
    """Property changes can be observed."""

    assert property_fragment.observable

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_fragment)

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

    run_test_coroutine(test_coroutine)


def test_on_property_change_non_observable(exposed_thing):
    """Observe requests to non-observable properties are rejected."""

    prop_init_non_observable = PropertyFragmentDict({
        "type": "string",
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

    run_test_coroutine(test_coroutine)


def test_on_event(exposed_thing, event_fragment):
    """Events defined in the Thing Description can be observed."""

    event_name = Faker().pystr()
    exposed_thing.add_event(event_name, event_fragment)

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


def test_on_td_change(exposed_thing, property_fragment, event_fragment, action_fragment):
    """Thing Description changes can be observed."""

    def subscribe_func(*args, **kwargs):
        return exposed_thing.on_td_change().subscribe(*args, **kwargs)

    _test_td_change_events(exposed_thing, property_fragment, event_fragment, action_fragment, subscribe_func)


def test_thing_property_get(exposed_thing, property_fragment):
    """Property values can be retrieved on ExposedThings using the map-like interface."""

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        prop_init_value = Faker().sentence()
        exposed_thing.add_property(prop_name, property_fragment, value=prop_init_value)
        value = yield exposed_thing.properties[prop_name].read()
        assert value == prop_init_value

    run_test_coroutine(test_coroutine)


def test_thing_property_set(exposed_thing, property_fragment):
    """Property values can be updated on ExposedThings using the map-like interface."""

    assert property_fragment.writable

    @tornado.gen.coroutine
    def test_coroutine():
        updated_val = Faker().pystr()
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_fragment)
        yield exposed_thing.properties[prop_name].write(updated_val)
        value = yield exposed_thing.properties[prop_name].read()
        assert value == updated_val

    run_test_coroutine(test_coroutine)


def test_thing_property_subscribe(exposed_thing, property_fragment):
    """Property updates can be observed on ExposedThings using the map-like interface."""

    assert property_fragment.observable

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_fragment)

        values = [Faker().sentence() for _ in range(10)]
        values_futures = {key: Future() for key in values}

        def on_next(ev):
            value = ev.data.value
            if value in values_futures and not values_futures[value].done():
                values_futures[value].set_result(True)

        subscription = exposed_thing.properties[prop_name].subscribe(on_next)

        yield tornado.gen.sleep(0)

        for val in values:
            yield exposed_thing.properties[prop_name].write(val)

        yield [future for future in six.itervalues(values_futures)]

        subscription.dispose()

    run_test_coroutine(test_coroutine)


def test_thing_property_getters(exposed_thing, property_fragment):
    """ThingProperty retrieved from ExposedThing expose the attributes
    from the Interaction, InteractionFragment and PropertyFragment interfaces."""

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        prop_init_value = Faker().sentence()
        exposed_thing.add_property(prop_name, property_fragment, value=prop_init_value)
        thing_property = exposed_thing.properties[prop_name]

        assert len(thing_property.forms) == 0
        assert thing_property.title == property_fragment.title
        assert thing_property.description == property_fragment.description
        assert thing_property.observable == property_fragment.observable
        assert thing_property.type == property_fragment.type

    run_test_coroutine(test_coroutine)


def test_thing_action_run(exposed_thing, action_fragment):
    """Actions can be invoked on ExposedThings using the map-like interface."""

    @tornado.gen.coroutine
    def lower(parameters):
        input_value = parameters.get("input")
        raise tornado.gen.Return(str(input_value).lower())

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = Faker().pystr()
        exposed_thing.add_action(action_name, action_fragment, lower)
        input_value = Faker().pystr()

        result = yield exposed_thing.actions[action_name].invoke(input_value)
        result_expected = yield exposed_thing.invoke_action(action_name, input_value)

        assert result == result_expected

    run_test_coroutine(test_coroutine)


def test_thing_action_getters(exposed_thing, action_fragment):
    """ThingAction retrieved from ExposedThing expose the attributes
    from the Interaction, InteractionFragment and ActionFragment interfaces."""

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = Faker().pystr()
        exposed_thing.add_action(action_name, action_fragment)
        thing_action = exposed_thing.actions[action_name]

        assert len(thing_action.forms) == 0
        assert thing_action.title == action_fragment.title
        assert thing_action.description == action_fragment.description
        assert thing_action.input.type == action_fragment.input.type
        assert thing_action.output.type == action_fragment.output.type

    run_test_coroutine(test_coroutine)


def test_thing_event_subscribe(exposed_thing, event_fragment):
    """Property updates can be observed on ExposedThings using the map-like interface."""

    @tornado.gen.coroutine
    def test_coroutine():
        event_name = Faker().pystr()
        exposed_thing.add_event(event_name, event_fragment)

        values = [Faker().sentence() for _ in range(10)]
        values_futures = {key: Future() for key in values}

        def on_next(ev):
            value = ev.data
            if value in values_futures and not values_futures[value].done():
                values_futures[value].set_result(True)

        subscription = exposed_thing.events[event_name].subscribe(on_next)

        yield tornado.gen.sleep(0)

        for val in values:
            yield exposed_thing.events[event_name].emit(val)

        yield [future for future in six.itervalues(values_futures)]

        subscription.dispose()

    run_test_coroutine(test_coroutine)


def test_thing_event_getters(exposed_thing, event_fragment):
    """ThingEvent retrieved from ExposedThing expose the attributes
    from the Interaction, InteractionFragment and EventFragment interfaces."""

    @tornado.gen.coroutine
    def test_coroutine():
        event_name = Faker().pystr()
        exposed_thing.add_event(event_name, event_fragment)
        thing_event = exposed_thing.events[event_name]

        assert len(thing_event.forms) == 0
        assert thing_event.title == event_fragment.title
        assert thing_event.description == event_fragment.description
        assert thing_event.data.type == event_fragment.data.type

    run_test_coroutine(test_coroutine)


def test_set_property_read_handler(exposed_thing, property_fragment):
    """Read handlers can be defined for ExposedThing property interactions."""

    const_prop_value = Faker().sentence()

    @tornado.gen.coroutine
    def read_handler():
        raise tornado.gen.Return(const_prop_value)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_fragment)
        exposed_thing.set_property_read_handler(prop_name, read_handler)
        value = yield exposed_thing.properties[prop_name].read()
        assert value == const_prop_value

    run_test_coroutine(test_coroutine)


def test_set_property_write_handler(exposed_thing, property_fragment):
    """Write handlers can be defined for ExposedThing property interactions."""

    prop_history = []

    @tornado.gen.coroutine
    def write_handler(value):
        yield tornado.gen.sleep(0)
        prop_history.append(value)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = Faker().pystr()
        exposed_thing.add_property(prop_name, property_fragment)
        exposed_thing.set_property_write_handler(prop_name, write_handler)
        prop_value = Faker().sentence()
        assert not len(prop_history)
        yield exposed_thing.properties[prop_name].write(prop_value)
        assert prop_value in prop_history

    run_test_coroutine(test_coroutine)


def test_subscribe(exposed_thing, property_fragment, event_fragment, action_fragment):
    """Subscribing to the ExposedThing provides Thing Description update events."""

    def subscribe_func(*args, **kwargs):
        return exposed_thing.subscribe(*args, **kwargs)

    _test_td_change_events(exposed_thing, property_fragment, event_fragment, action_fragment, subscribe_func)


def test_thing_interaction_dict_behaviour(exposed_thing, property_fragment):
    """The Interactions dict-like interface of an ExposedThing behaves like a dict."""

    prop_name = Faker().pystr()
    exposed_thing.add_property(prop_name, property_fragment)

    assert len(exposed_thing.properties) == 1
    assert prop_name in exposed_thing.properties
    assert next(key for key in exposed_thing.properties if key == prop_name)


def test_thing_fragment_getters_setters():
    """ThingFragment attributes can be get and set from the ExposedThing."""

    thing_fragment = ThingFragment({
        "id": uuid.uuid4().urn,
        "name": Faker().pystr(),
        "description": Faker().pystr(),
        "properties": {
            uuid.uuid4().hex: {
                "description": Faker().pystr(),
                "type": DataType.STRING
            }
        }
    })

    thing = Thing(thing_fragment=thing_fragment)
    exp_thing = ExposedThing(servient=Servient(), thing=thing)

    assert exp_thing.name == thing_fragment.name
    assert exp_thing.description == thing_fragment.description
    assert list(exp_thing.properties) == list(six.iterkeys(thing_fragment.properties))

    name_original = thing_fragment.name
    name_updated = Faker().pystr()

    description_original = thing_fragment.description
    description_updated = Faker().pystr()

    exp_thing.name = name_updated
    exp_thing.description = description_updated

    assert exp_thing.name == name_updated
    assert exp_thing.name != name_original
    assert exp_thing.description == description_updated
    assert exp_thing.description != description_original

    with pytest.raises(AttributeError):
        # noinspection PyPropertyAccess
        exp_thing.id = Faker().pystr()

    with pytest.raises(AttributeError):
        # noinspection PyPropertyAccess
        exp_thing.properties = Faker().pylist()

    with pytest.raises(AttributeError):
        # noinspection PyPropertyAccess
        exp_thing.actions = Faker().pylist()

    with pytest.raises(AttributeError):
        # noinspection PyPropertyAccess
        exp_thing.events = Faker().pylist()


def _test_equivalent_interaction_names(base_name, transform_name):
    """Helper function to test that interaction names
    are equivalent given a certain transformation function."""

    thing = Thing(id=uuid.uuid4().urn)
    exp_thing = ExposedThing(servient=Servient(), thing=thing)

    prop_name = "property" + base_name
    prop_name_transform = transform_name(prop_name)

    prop_default_value = Faker().pybool()
    exp_thing.add_property(prop_name, {"type": DataType.BOOLEAN}, value=prop_default_value)

    with pytest.raises(ValueError):
        exp_thing.add_property(prop_name_transform, {"type": DataType.BOOLEAN})

    @tornado.gen.coroutine
    def assert_prop_read():
        assert (yield exp_thing.properties[prop_name].read()) is prop_default_value
        assert (yield exp_thing.properties[prop_name_transform].read()) is prop_default_value

    tornado.ioloop.IOLoop.current().run_sync(assert_prop_read)

    action_name = "action" + base_name
    action_name_transform = transform_name(action_name)

    exp_thing.add_action(action_name, {})

    with pytest.raises(ValueError):
        exp_thing.add_action(action_name_transform, {})

    assert exp_thing.actions[action_name]
    assert exp_thing.actions[action_name_transform]

    event_name = "event" + base_name
    event_name_transform = transform_name(event_name)

    exp_thing.add_event(event_name, {})

    with pytest.raises(ValueError):
        exp_thing.add_event(event_name_transform, {})

    assert exp_thing.events[event_name]
    assert exp_thing.events[event_name_transform]


def test_interaction_name_case_insensitive():
    """ExposedThing interaction names are equivalent in a case-insensitive fashion."""

    _test_equivalent_interaction_names("camelCaseStr", lambda name: name.lower())
    _test_equivalent_interaction_names("camelCaseStr", lambda name: name.upper())
    _test_equivalent_interaction_names("camelCaseStr", lambda name: name.title())


def test_interaction_name_url_safe():
    """ExposedThing interaction names are equivalent in a URL-safe fashion."""

    _test_equivalent_interaction_names("url_UnSafE-Str", lambda name: slugify(name))
