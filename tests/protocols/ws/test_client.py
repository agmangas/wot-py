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

from wotpy.protocols.ws.client import WebsocketClient, ProtocolClientException
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.description import ThingDescription
from wotpy.wot.servient import Servient


def build_websocket_servient():
    """Builds, starts and returns an ExposedThing and the Servient that contains it."""

    ws_port = random.randint(20000, 40000)
    ws_server = WebsocketServer(port=ws_port)

    servient = Servient()
    servient.add_server(ws_server)

    wot = servient.start()

    property_name = uuid.uuid4().hex
    action_name = uuid.uuid4().hex
    event_name = uuid.uuid4().hex

    td = ThingDescription(doc={
        "id": uuid.uuid4().urn,
        "properties": {
            property_name: {
                "writable": True,
                "observable": True,
                "type": "string"
            }
        },
        "actions": {
            action_name: {
                "writable": True,
                "observable": True,
                "input": "string",
                "output": "string"
            }
        },
        "events": {
            event_name: {
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

    exposed_thing.set_action_handler(action_handler=action_handler, action_name=action_name)

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
def test_on_property_change():
    """The Websockets client can observe property changes."""

    servient, exposed_thing, td = build_websocket_servient()

    @tornado.gen.coroutine
    def test_coroutine():
        ws_client = WebsocketClient()

        prop_name = next(six.iterkeys(td.properties))

        observable = ws_client.on_property_change(td, prop_name)

        prop_values = [uuid.uuid4().hex for _ in range(20)]
        future_values = {key: tornado.concurrent.Future() for key in prop_values}
        future_conn = tornado.concurrent.Future()

        def on_next(ev):
            if not future_conn.done():
                future_conn.set_result(True)

            new_prop_value = ev.data.value

            if new_prop_value in future_values:
                future_values[new_prop_value].set_result(True)

        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        while not future_conn.done():
            yield exposed_thing.write_property(prop_name, uuid.uuid4().hex)
            yield tornado.gen.sleep(0.1)

        for val in prop_values:
            yield exposed_thing.write_property(prop_name, val)

        yield list(future_values.values())

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
