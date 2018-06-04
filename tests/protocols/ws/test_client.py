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

    return servient, exposed_thing


def run_websocket_client_test(test_coroutine):
    """Runs the given test coroutine in the context of a Servient with a Websockets server."""

    servient, exposed_thing = build_websocket_servient()

    io_loop = tornado.ioloop.IOLoop.current()
    future_result = tornado.concurrent.Future()
    td = ThingDescription.from_thing(exposed_thing.thing)

    # noinspection PyBroadException
    @tornado.gen.coroutine
    def test_coroutine_wrapper(*args, **kwargs):
        try:
            yield test_coroutine(*args, **kwargs)
        except Exception as ex:
            future_result.set_exception(ex)

    # noinspection PyBroadException
    @tornado.gen.coroutine
    def stop_loop():
        """Stops the IOLoop when the result Future completes."""

        try:
            yield future_result
        except Exception:
            pass

        io_loop.stop()

    test_coroutine_kwargs = {
        "future_result": future_result,
        "exposed_thing": exposed_thing,
        "td": td
    }

    io_loop.add_callback(test_coroutine_wrapper, **test_coroutine_kwargs)
    io_loop.add_callback(stop_loop)
    io_loop.start()

    assert future_result.result()


@pytest.mark.flaky(reruns=5)
def test_read_property():
    """The Websockets client is able to read properties."""

    @tornado.gen.coroutine
    def test_coroutine(future_result, exposed_thing, td):
        ws_client = WebsocketClient()

        prop_name = next(six.iterkeys(td.properties))
        prop_value = uuid.uuid4().hex

        yield exposed_thing.write_property(prop_name, prop_value)

        result = yield ws_client.read_property(td, prop_name)

        assert result == prop_value

        future_result.set_result(True)

    run_websocket_client_test(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_read_property_unknown():
    """The Websockets client raises an error when attempting to read an unknown property."""

    @tornado.gen.coroutine
    def test_coroutine(future_result, exposed_thing, td):
        ws_client = WebsocketClient()

        with pytest.raises(ProtocolClientException):
            yield ws_client.read_property(td, uuid.uuid4().hex)

        future_result.set_result(True)

    run_websocket_client_test(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_write_property():
    """The Websockets client is able to write properties."""

    @tornado.gen.coroutine
    def test_coroutine(future_result, exposed_thing, td):
        ws_client = WebsocketClient()

        prop_name = next(six.iterkeys(td.properties))
        prop_value = uuid.uuid4().hex

        yield ws_client.write_property(td, prop_name, prop_value)

        curr_value = yield exposed_thing.read_property(prop_name)

        assert curr_value == prop_value

        future_result.set_result(True)

    run_websocket_client_test(test_coroutine)
