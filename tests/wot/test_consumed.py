#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import six
import tornado.gen
import tornado.ioloop
from faker import Faker
from rx.concurrency import IOLoopScheduler
from tornado.concurrent import Future

from tests.utils import find_free_port, run_test_coroutine
from wotpy.protocols.http.client import HTTPClient
from wotpy.protocols.http.server import HTTPServer
from wotpy.protocols.ws.client import WebsocketClient
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription


def _test_property_change_events(exposed_thing, subscribe_func):
    """Helper function to test client subscriptions to property change events."""

    @tornado.gen.coroutine
    def test_coroutine():
        td = ThingDescription.from_thing(exposed_thing.thing)
        prop_name = next(six.iterkeys(td.properties))

        future_conn = Future()
        future_change = Future()

        prop_value = Faker().sentence()

        def on_next(ev):
            if not future_conn.done():
                future_conn.set_result(True)
                return

            if ev.data.value == prop_value:
                future_change.set_result(True)

        subscription = subscribe_func(prop_name, on_next)

        while not future_conn.done():
            yield tornado.gen.sleep(0)
            yield exposed_thing.write_property(prop_name, Faker().sentence())

        yield exposed_thing.write_property(prop_name, prop_value)

        yield future_change

        assert future_change.result()

        subscription.dispose()

    run_test_coroutine(test_coroutine)


def _test_event_emission_events(exposed_thing, subscribe_func):
    """Helper function to test client subscription to event emissions."""

    @tornado.gen.coroutine
    def test_coroutine():
        td = ThingDescription.from_thing(exposed_thing.thing)
        event_name = next(six.iterkeys(td.events))

        future_conn = Future()
        future_event = Future()

        payload = Faker().sentence()

        def on_next(ev):
            if not future_conn.done():
                future_conn.set_result(True)
                return

            if ev.data == payload:
                future_event.set_result(True)

        subscription = subscribe_func(event_name, on_next)

        while not future_conn.done():
            yield tornado.gen.sleep(0)
            exposed_thing.emit_event(event_name, Faker().sentence())

        exposed_thing.emit_event(event_name, payload)

        yield future_event

        assert future_event.result()

        subscription.dispose()

    run_test_coroutine(test_coroutine)


def test_thing_template_getters(consumed_exposed_pair):
    """ThingTemplate properties can be accessed from the ConsumedThing."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    thing_template = consumed_thing.td.to_thing_fragment()

    assert consumed_thing.id == thing_template.id
    assert consumed_thing.name == thing_template.name
    assert consumed_thing.description == thing_template.description


def test_read_property(consumed_exposed_pair):
    """A ConsumedThing is able to read properties."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(consumed_thing.td.properties))

        result_exposed = yield exposed_thing.read_property(prop_name)
        result_consumed = yield consumed_thing.read_property(prop_name)

        assert result_consumed == result_exposed

    run_test_coroutine(test_coroutine)


def test_write_property(consumed_exposed_pair):
    """A ConsumedThing is able to write properties."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(consumed_thing.td.properties))

        val_01 = Faker().sentence()
        val_02 = Faker().sentence()

        yield exposed_thing.write_property(prop_name, val_01)
        value = yield exposed_thing.read_property(prop_name)

        assert value == val_01

        yield consumed_thing.write_property(prop_name, val_02)
        value = yield exposed_thing.read_property(prop_name)

        assert value == val_02

    run_test_coroutine(test_coroutine)


def test_invoke_action(consumed_exposed_pair):
    """A ConsumedThing is able to invoke actions."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = next(six.iterkeys(consumed_thing.td.actions))

        input_value = Faker().pystr()
        result = yield consumed_thing.invoke_action(action_name, input_value)
        result_expected = yield exposed_thing.invoke_action(action_name, input_value)

        assert result == result_expected

    run_test_coroutine(test_coroutine)


def test_on_event(consumed_exposed_pair):
    """A ConsumedThing is able to observe events."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    def subscribe_func(event_name, on_next):
        observable = consumed_thing.on_event(event_name)
        return observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

    _test_event_emission_events(exposed_thing, subscribe_func)


def test_on_property_change(consumed_exposed_pair):
    """A ConsumedThing is able to observe property updates."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    def subscribe_func(prop_name, on_next):
        observable = consumed_thing.on_property_change(prop_name)
        return observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

    _test_property_change_events(exposed_thing, subscribe_func)


def test_thing_property_get(consumed_exposed_pair):
    """Property values can be retrieved on ConsumedThings using the map-like interface."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(consumed_thing.td.properties))

        result_exposed = yield exposed_thing.read_property(prop_name)
        result_consumed = yield consumed_thing.properties[prop_name].read()

        assert result_consumed == result_exposed

    run_test_coroutine(test_coroutine)


def test_thing_property_set(consumed_exposed_pair):
    """Property values can be updated on ConsumedThings using the map-like interface."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(consumed_thing.td.properties))
        updated_value = Faker().sentence()
        curr_value = yield exposed_thing.read_property(prop_name)

        assert consumed_thing.td.properties[prop_name].writable
        assert curr_value != updated_value

        yield consumed_thing.properties[prop_name].write(updated_value)
        result_exposed = yield exposed_thing.read_property(prop_name)

        assert result_exposed == updated_value

    run_test_coroutine(test_coroutine)


def test_thing_property_subscribe(consumed_exposed_pair):
    """Property updates can be observed on ConsumedThings using the map-like interface."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    def subscribe_func(prop_name, on_next):
        return consumed_thing.properties[prop_name].subscribe(on_next)

    _test_property_change_events(exposed_thing, subscribe_func)


def test_thing_property_getters(consumed_exposed_pair):
    """ThingProperty retrieved from ConsumedThing expose the attributes
    from the Interaction, InteractionFragment and PropertyFragment interfaces."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(consumed_thing.td.properties))
        thing_prop_con = consumed_thing.properties[prop_name]
        thing_prop_exp = exposed_thing.properties[prop_name]

        assert len(thing_prop_con.forms) == 0
        assert thing_prop_con.title == thing_prop_exp.title
        assert thing_prop_con.description == thing_prop_exp.description
        assert thing_prop_con.observable == thing_prop_exp.observable
        assert thing_prop_con.type == thing_prop_exp.type

    run_test_coroutine(test_coroutine)


def test_thing_action_run(consumed_exposed_pair):
    """Actions can be invoked on ConsumedThings using the map-like interface."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = next(six.iterkeys(consumed_thing.td.actions))

        input_value = Faker().pystr()
        result = yield consumed_thing.actions[action_name].invoke(input_value)
        result_expected = yield exposed_thing.invoke_action(action_name, input_value)

        assert result == result_expected

    run_test_coroutine(test_coroutine)


def test_thing_action_getters(consumed_exposed_pair):
    """ThingAction retrieved from ConsumedThing expose the attributes
    from the Interaction, InteractionFragment and ActionFragment interfaces."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        action_name = next(six.iterkeys(consumed_thing.td.actions))
        thing_action_con = consumed_thing.actions[action_name]
        thing_action_exp = exposed_thing.actions[action_name]

        assert len(thing_action_con.forms) == 0
        assert thing_action_con.title == thing_action_exp.title
        assert thing_action_con.description == thing_action_exp.description
        assert thing_action_con.input.type == thing_action_exp.input.type
        assert thing_action_con.output.type == thing_action_exp.output.type

    run_test_coroutine(test_coroutine)


def test_thing_event_subscribe(consumed_exposed_pair):
    """Property updates can be observed on ConsumedThings using the map-like interface."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    def subscribe_func(event_name, on_next):
        return consumed_thing.events[event_name].subscribe(on_next)

    _test_event_emission_events(exposed_thing, subscribe_func)


def test_thing_event_getters(consumed_exposed_pair):
    """ThingEvent retrieved from ConsumedThing expose the attributes
    from the Interaction, InteractionFragment and EventFragment interfaces."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")
    exposed_thing = consumed_exposed_pair.pop("exposed_thing")

    @tornado.gen.coroutine
    def test_coroutine():
        event_name = next(six.iterkeys(consumed_thing.td.events))
        thing_event_con = consumed_thing.events[event_name]
        thing_event_exp = exposed_thing.events[event_name]

        assert len(thing_event_con.forms) == 0
        assert thing_event_con.title == thing_event_exp.title
        assert thing_event_con.description == thing_event_exp.description
        assert thing_event_con.data.type == thing_event_exp.data.type

    run_test_coroutine(test_coroutine)


def test_thing_interaction_dict_behaviour(consumed_exposed_pair):
    """The Interactions dict-like interface of a ConsumedThing behaves like a dict."""

    consumed_thing = consumed_exposed_pair.pop("consumed_thing")

    prop_name = next((key for key in consumed_thing.properties), None)

    assert prop_name
    assert len(consumed_thing.properties) > 0
    assert prop_name in consumed_thing.properties


def test_consumed_client_protocols_preference():
    """The Servient selects different protocol clients to consume Things
    depending on the protocol choices displayed on the Thing Description."""

    servient = Servient(catalogue_port=None)

    @tornado.gen.coroutine
    def servient_start():
        raise tornado.gen.Return((yield servient.start()))

    @tornado.gen.coroutine
    def servient_shutdown():
        yield servient.shutdown()

    http_port = find_free_port()
    http_server = HTTPServer(port=http_port)

    servient.add_server(http_server)

    ws_port = find_free_port()
    ws_server = WebsocketServer(port=ws_port)

    servient.add_server(ws_server)

    client_server_map = {
        HTTPClient: http_server,
        WebsocketClient: ws_server
    }

    wot = tornado.ioloop.IOLoop.current().run_sync(servient_start)

    prop_name = uuid.uuid4().hex

    td_produce = ThingDescription({
        "id": uuid.uuid4().urn,
        "name": uuid.uuid4().hex,
        "properties": {
            prop_name: {
                "observable": True,
                "type": "string"
            }
        }
    })

    exposed_thing = wot.produce(td_produce.to_str())
    exposed_thing.expose()

    td_forms_all = ThingDescription.from_thing(exposed_thing.thing)

    client_01 = servient.select_client(td_forms_all, prop_name)
    client_01_class = client_01.__class__

    assert client_01_class in six.iterkeys(client_server_map)

    tornado.ioloop.IOLoop.current().run_sync(servient_shutdown)
    servient.remove_server(client_server_map[client_01_class].protocol)
    tornado.ioloop.IOLoop.current().run_sync(servient_start)

    td_forms_removed = ThingDescription.from_thing(exposed_thing.thing)

    client_02 = servient.select_client(td_forms_removed, prop_name)
    client_02_class = client_02.__class__

    assert client_02_class != client_01_class
    assert client_02_class in six.iterkeys(client_server_map)

    tornado.ioloop.IOLoop.current().run_sync(servient_shutdown)
