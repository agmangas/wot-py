#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
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

from wotpy.protocols.ws.client import WebsocketClient, ProtocolClientException
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.description import ThingDescription
from wotpy.wot.dictionaries import ThingActionInit
from wotpy.wot.servient import Servient


def build_websocket_servient():
    """Builds, starts and returns an ExposedThing and the Servient that contains it."""

    ws_port = random.randint(20000, 40000)
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient()
    servient.add_server(ws_server)

    wot = servient.start()

    property_name_01 = uuid.uuid4().hex
    property_name_02 = uuid.uuid4().hex
    action_name_01 = uuid.uuid4().hex
    event_name_01 = uuid.uuid4().hex

    td = ThingDescription(doc={
        "id": uuid.uuid4().urn,
        "properties": {
            property_name_01: {
                "writable": True,
                "observable": True,
                "type": "string"
            },
            property_name_02: {
                "writable": True,
                "observable": True,
                "type": "string"
            }
        },
        "actions": {
            action_name_01: {
                "writable": True,
                "observable": True,
                "input": "string",
                "output": "string"
            }
        },
        "events": {
            event_name_01: {
                "type": "string"
            }
        },
    })

    exposed_thing = wot.produce(td.to_str())
    exposed_thing.start()

    @tornado.gen.coroutine
    def action_handler(arg_a, arg_b=None):
        arg_b = arg_b or uuid.uuid4().hex
        raise tornado.gen.Return(arg_a + arg_b)

    exposed_thing.set_action_handler(action_handler=action_handler, action_name=action_name_01)

    td = ThingDescription.from_thing(exposed_thing.thing)

    return servient, exposed_thing, td


@pytest.mark.flaky(reruns=5)
def test_read_property():
    """The Websockets client can read properties."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        ws_client = WebsocketClient()

        prop_name = next(six.iterkeys(td.properties))
        prop_value = uuid.uuid4().hex

        yield exposed_thing.write_property(prop_name, prop_value)

        result = yield ws_client.read_property(td, prop_name)

        assert result == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_read_property_unknown():
    """The Websockets client raises an error when attempting to read an unknown property."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        ws_client = WebsocketClient()

        with pytest.raises(ProtocolClientException):
            yield ws_client.read_property(td, uuid.uuid4().hex)

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_write_property():
    """The Websockets client can write properties."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        ws_client = WebsocketClient()

        prop_name = next(six.iterkeys(td.properties))
        prop_value = uuid.uuid4().hex

        yield ws_client.write_property(td, prop_name, prop_value)

        curr_value = yield exposed_thing.read_property(prop_name)

        assert curr_value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_invoke_action():
    """The Websockets client can invoke actions."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        ws_client = WebsocketClient()

        action_name = next(six.iterkeys(td.actions))

        arg_a = uuid.uuid4().hex
        arg_b = uuid.uuid4().hex

        result = yield ws_client.invoke_action(td, action_name, arg_a=arg_a, arg_b=arg_b)

        assert result == arg_a + arg_b

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_event():
    """The Websockets client can observe events."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        ws_client = WebsocketClient()

        event_name = next(six.iterkeys(td.events))

        observable = ws_client.on_event(td, event_name)

        payloads = [uuid.uuid4().hex for _ in range(10)]
        future_payloads = {key: Future() for key in payloads}
        future_conn = Future()

        def on_next(ev):
            if not future_conn.done():
                future_conn.set_result(True)

            if ev.data in future_payloads:
                future_payloads[ev.data].set_result(True)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        while not future_conn.done():
            yield exposed_thing.emit_event(event_name, uuid.uuid4().hex)
            yield tornado.gen.sleep(0.1)

        for payload in future_payloads:
            yield exposed_thing.emit_event(event_name, payload)

        yield list(future_payloads.values())

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_property_change():
    """The Websockets client can observe property changes."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        ws_client = WebsocketClient()

        prop_names = list(td.properties.keys())
        prop_name_01 = prop_names[0]
        prop_name_02 = prop_names[1]

        obsv_01 = ws_client.on_property_change(td, prop_name_01)
        obsv_02 = ws_client.on_property_change(td, prop_name_02)

        prop_values_01 = [uuid.uuid4().hex for _ in range(10)]
        prop_values_02 = [uuid.uuid4().hex for _ in range(90)]

        future_values_01 = {key: Future() for key in prop_values_01}
        future_values_02 = {key: Future() for key in prop_values_02}

        future_conn_01 = Future()
        future_conn_02 = Future()

        def build_on_next(fut_conn, fut_vals):
            def on_next(ev):
                if not fut_conn.done():
                    fut_conn.set_result(True)

                if ev.data.value in fut_vals:
                    fut_vals[ev.data.value].set_result(True)

            return on_next

        on_next_01 = build_on_next(future_conn_01, future_values_01)
        on_next_02 = build_on_next(future_conn_02, future_values_02)

        subscription_01 = obsv_01.subscribe_on(IOLoopScheduler()).subscribe(on_next_01)
        subscription_02 = obsv_02.subscribe_on(IOLoopScheduler()).subscribe(on_next_02)

        while not future_conn_01.done() or not future_conn_02.done():
            yield exposed_thing.write_property(prop_name_01, uuid.uuid4().hex)
            yield exposed_thing.write_property(prop_name_02, uuid.uuid4().hex)
            yield tornado.gen.sleep(0.1)

        assert len(prop_values_01) < len(prop_values_02)

        for idx in range(len(prop_values_01)):
            yield exposed_thing.write_property(prop_name_01, prop_values_01[idx])
            yield exposed_thing.write_property(prop_name_02, prop_values_02[idx])

        yield list(future_values_01.values())

        assert next(fut for fut in six.itervalues(future_values_02) if not fut.done())

        subscription_01.dispose()

        for val in prop_values_02[len(prop_values_01):]:
            yield exposed_thing.write_property(prop_name_02, val)

        yield list(future_values_02.values())

        subscription_02.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_td_change_undefined_base_url():
    """Attempting to observe changes using the Websockets
    client on a TD without a base URL throws an error."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        future_err = Future()

        def on_error(err):
            assert isinstance(err, ProtocolClientException)
            future_err.set_result(True)

        ws_client = WebsocketClient()
        ws_client.on_td_change(td).subscribe(on_error=on_error)

        yield future_err

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_td_change():
    """The Websockets client can observe Thing Description changes."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        ws_client = WebsocketClient()

        prop_name = next(six.iterkeys(td.properties))
        prop_href = td.get_property_forms(prop_name)[0]["href"]
        base_url = prop_href.replace("ws", "http")

        td.doc.update({"base": base_url})

        action_init = ThingActionInit(
            name=uuid.uuid4().hex,
            input_data_description="string",
            output_data_description="string")

        observable = ws_client.on_td_change(td)

        future_change = Future()
        future_conn = Future()

        def on_next(ev):
            if not future_conn.done():
                future_conn.set_result(True)

            if ev.data.name == action_init.name:
                future_change.set_result(True)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        while not future_conn.done():
            exposed_thing.add_action(ThingActionInit(name=uuid.uuid4().hex))
            yield tornado.gen.sleep(0.1)

        assert not future_change.done()

        exposed_thing.add_action(action_init)

        yield future_change

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
