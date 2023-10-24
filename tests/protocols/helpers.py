#!/usr/bin/env python
# -*- coding: utf-8 -*-

import asyncio
import logging
import random
import uuid

from faker import Faker
from rx.concurrency import IOLoopScheduler

from tests.utils import run_test_coroutine
from wotpy.wot.dictionaries.interaction import (
    ActionFragmentDict,
    EventFragmentDict,
    PropertyFragmentDict,
)
from wotpy.wot.td import ThingDescription


async def client_test_on_property_change_async(servient, protocol_client_cls):
    """Helper function to test observation of Property updates on bindings clients."""

    exposed_thing = next(servient.exposed_things)
    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(
        prop_name,
        PropertyFragmentDict({"type": "string", "observable": True}),
        value=Faker().sentence(),
    )

    servient.refresh_forms()
    td = ThingDescription.from_thing(exposed_thing.thing)
    protocol_client = protocol_client_cls()
    values = [Faker().sentence() for _ in range(10)]
    values_observed = {value: asyncio.Future() for value in values}
    stop_event = asyncio.Event()

    async def write_next():
        while not stop_event.is_set():
            try:
                try:
                    next_value = next(
                        val for val, fut in values_observed.items() if not fut.done()
                    )
                    await exposed_thing.properties[prop_name].write(next_value)
                except StopIteration:
                    logging.warning("Unexpected StopIteration", exc_info=True)
                await asyncio.sleep(0.01)
            except StopIteration:
                pass

    def on_next(ev):
        prop_value = ev.data.value
        if prop_value in values_observed and not values_observed[prop_value].done():
            values_observed[prop_value].set_result(True)

    observable = protocol_client.on_property_change(td, prop_name)
    subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)
    task_write = asyncio.create_task(write_next())
    await asyncio.gather(*list(values_observed.values()))
    stop_event.set()
    await task_write
    subscription.dispose()


def client_test_on_property_change(*args, **kwargs):
    async def test_coroutine():
        await client_test_on_property_change_async(*args, **kwargs)

    run_test_coroutine(test_coroutine)


async def client_test_on_event_async(servient, protocol_client_cls):
    """Helper function to test observation of Events on bindings clients."""

    exposed_thing = next(servient.exposed_things)
    event_name = uuid.uuid4().hex
    exposed_thing.add_event(event_name, EventFragmentDict({"type": "number"}))
    servient.refresh_forms()
    td = ThingDescription.from_thing(exposed_thing.thing)
    protocol_client = protocol_client_cls()
    payloads = [Faker().pyint() for _ in range(10)]
    future_payloads = {key: asyncio.Future() for key in payloads}
    stop_event = asyncio.Event()

    async def emit_next():
        while not stop_event.is_set():
            try:
                next_value = next(
                    val for val, fut in future_payloads.items() if not fut.done()
                )
                exposed_thing.events[event_name].emit(next_value)
            except StopIteration:
                logging.warning("Unexpected StopIteration", exc_info=True)
            await asyncio.sleep(0.01)

    def on_next(ev):
        if ev.data in future_payloads and not future_payloads[ev.data].done():
            future_payloads[ev.data].set_result(True)

    observable = protocol_client.on_event(td, event_name)
    subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)
    task_emit = asyncio.create_task(emit_next())
    await asyncio.gather(*list(future_payloads.values()))
    stop_event.set()
    await task_emit
    subscription.dispose()


def client_test_on_event(*args, **kwargs):
    async def test_coroutine():
        await client_test_on_event_async(*args, **kwargs)

    run_test_coroutine(test_coroutine)


async def client_test_read_property_async(servient, protocol_client_cls, timeout=None):
    """Helper function to test Property reads on bindings clients."""

    exposed_thing = next(servient.exposed_things)
    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(
        prop_name,
        PropertyFragmentDict({"type": "string", "observable": True}),
        value=Faker().sentence(),
    )

    servient.refresh_forms()
    td = ThingDescription.from_thing(exposed_thing.thing)
    protocol_client = protocol_client_cls()
    prop_value = Faker().sentence()

    curr_prop_value = await protocol_client.read_property(
        td, prop_name, timeout=timeout
    )

    assert curr_prop_value != prop_value

    await exposed_thing.properties[prop_name].write(prop_value)

    curr_prop_value = await protocol_client.read_property(
        td, prop_name, timeout=timeout
    )

    assert curr_prop_value == prop_value


def client_test_read_property(*args, **kwargs):
    async def test_coroutine():
        await client_test_read_property_async(*args, **kwargs)

    run_test_coroutine(test_coroutine)


async def client_test_write_property_async(servient, protocol_client_cls, timeout=None):
    """Helper function to test Property writes on bindings clients."""

    exposed_thing = next(servient.exposed_things)
    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(
        prop_name,
        PropertyFragmentDict({"type": "string", "observable": True}),
        value=Faker().sentence(),
    )

    servient.refresh_forms()
    td = ThingDescription.from_thing(exposed_thing.thing)
    protocol_client = protocol_client_cls()
    prop_value = Faker().sentence()
    prev_value = await exposed_thing.properties[prop_name].read()
    assert prev_value != prop_value
    await protocol_client.write_property(td, prop_name, prop_value, timeout=timeout)
    curr_value = await exposed_thing.properties[prop_name].read()
    assert curr_value == prop_value


def client_test_write_property(*args, **kwargs):
    async def test_coroutine():
        await client_test_write_property_async(*args, **kwargs)

    run_test_coroutine(test_coroutine)


async def client_test_invoke_action_async(servient, protocol_client_cls, timeout=None):
    """Helper function to test Action invocations on bindings clients."""

    exposed_thing = next(servient.exposed_things)
    action_name = uuid.uuid4().hex

    async def action_handler(parameters):
        input_value = parameters.get("input")
        await asyncio.sleep(random.random() * 0.1)
        return "{:f}".format(input_value)

    exposed_thing.add_action(
        action_name,
        ActionFragmentDict({"input": {"type": "number"}, "output": {"type": "string"}}),
        action_handler,
    )

    servient.refresh_forms()
    td = ThingDescription.from_thing(exposed_thing.thing)
    protocol_client = protocol_client_cls()
    input_value = Faker().pyint()

    result = await protocol_client.invoke_action(
        td, action_name, input_value, timeout=timeout
    )

    result_expected = await action_handler({"input": input_value})

    assert result == result_expected


def client_test_invoke_action(*args, **kwargs):
    async def test_coroutine():
        await client_test_invoke_action_async(*args, **kwargs)

    run_test_coroutine(test_coroutine)


async def client_test_invoke_action_error_async(servient, protocol_client_cls):
    """Helper function to test Action invocations that raise errors on bindings clients."""

    exposed_thing = next(servient.exposed_things)
    action_name = uuid.uuid4().hex
    err_message = Faker().sentence()

    def action_handler(parameters):
        raise ValueError(err_message)

    exposed_thing.add_action(
        action_name,
        ActionFragmentDict({"input": {"type": "number"}, "output": {"type": "string"}}),
        action_handler,
    )

    servient.refresh_forms()
    td = ThingDescription.from_thing(exposed_thing.thing)
    protocol_client = protocol_client_cls()

    try:
        await protocol_client.invoke_action(td, action_name, Faker().pyint())
        raise AssertionError("Did not raise Exception")
    except Exception as ex:
        assert err_message in str(ex)


def client_test_invoke_action_error(*args, **kwargs):
    async def test_coroutine():
        await client_test_invoke_action_error_async(*args, **kwargs)

    run_test_coroutine(test_coroutine)


async def client_test_on_property_change_error_async(servient, protocol_client_cls):
    """Helper function to test propagation of errors raised
    during observation of Property updates on bindings clients."""

    exposed_thing = next(servient.exposed_things)
    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(
        prop_name,
        PropertyFragmentDict({"type": "string", "observable": True}),
        value=Faker().sentence(),
    )

    servient.refresh_forms()
    td = ThingDescription.from_thing(exposed_thing.thing)
    protocol_client = protocol_client_cls()
    await servient.shutdown()
    future_err = asyncio.Future()

    def on_next(item):
        future_err.set_exception(Exception("Should not have emitted any items"))

    def on_error(err):
        future_err.set_result(err)

    observable = protocol_client.on_property_change(td, prop_name)
    subscribe_kwargs = {"on_next": on_next, "on_error": on_error}

    subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(
        **subscribe_kwargs
    )

    observe_err = await future_err
    assert isinstance(observe_err, Exception)
    subscription.dispose()


def client_test_on_property_change_error(*args, **kwargs):
    async def test_coroutine():
        await client_test_on_property_change_error_async(*args, **kwargs)

    run_test_coroutine(test_coroutine)
