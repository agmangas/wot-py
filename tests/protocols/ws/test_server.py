#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import random
import re
import time
import uuid

# noinspection PyPackageRequirements
import pytest
import tornado.gen
import tornado.ioloop
import tornado.testing
import tornado.websocket
# noinspection PyPackageRequirements
from faker import Faker
from six.moves.urllib.parse import urlparse, urlunparse

from wotpy.protocols.ws.enums import WebsocketMethods, WebsocketErrors
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageResponse, \
    WebsocketMessageError, \
    WebsocketMessageEmittedItem
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.td.thing import Thing
from wotpy.wot.dictionaries import ThingPropertyInit, ThingEventInit, ThingActionInit
from wotpy.wot.exposed import ExposedThing
from wotpy.wot.servient import Servient


def build_websocket_url(exposed_thing, ws_server, server_port):
    """Returns the WS connection URL for the given ExposedThing."""

    base_url = ws_server.build_base_url(hostname="localhost", thing=exposed_thing.thing)
    parsed_url = urlparse(base_url)
    test_netloc = re.sub(r':(\d+)$', ':{}'.format(server_port), parsed_url.netloc)

    test_url_parts = list(parsed_url)
    test_url_parts[1] = test_netloc

    return urlunparse(test_url_parts)


def build_websocket_server():
    """Builds a WebsocketServer instance with some ExposedThings."""

    fake = Faker()

    servient = Servient()

    thing_01_id = uuid.uuid4().urn
    thing_02_id = uuid.uuid4().urn

    exposed_thing_01 = ExposedThing(servient=servient, thing=Thing(id=thing_01_id))
    exposed_thing_02 = ExposedThing(servient=servient, thing=Thing(id=thing_02_id))

    prop_init_01 = ThingPropertyInit(
        name=uuid.uuid4().hex,
        value=fake.pystr(),
        data_type={"type": "string"})

    prop_init_02 = ThingPropertyInit(
        name=uuid.uuid4().hex,
        value=fake.pystr(),
        data_type={"type": "string"})

    prop_init_03 = ThingPropertyInit(
        name=uuid.uuid4().hex,
        value=fake.pystr(),
        data_type={"type": "string"})

    event_init_01 = ThingEventInit(
        name=uuid.uuid4().hex,
        data_description={"type": "object"})

    action_init_01 = ThingActionInit(
        name=uuid.uuid4().hex,
        input_data_description={"type": "string"},
        output_data_description={"type": "string"})

    def async_lower(val):
        loop = tornado.ioloop.IOLoop.current()
        return loop.run_in_executor(None, lambda x: time.sleep(0.1) or x.lower(), val)

    exposed_thing_01.add_property(prop_init_01)
    exposed_thing_01.add_property(prop_init_02)
    exposed_thing_01.add_event(event_init_01)
    exposed_thing_01.add_action(action_init_01)
    exposed_thing_01.set_action_handler(async_lower, action_init_01.name)

    exposed_thing_02.add_property(prop_init_03)

    ws_port = random.randint(20000, 40000)

    ws_server = WebsocketServer(port=ws_port)
    ws_server.add_exposed_thing(exposed_thing_01)
    ws_server.add_exposed_thing(exposed_thing_02)
    ws_server.start()

    url_thing_01 = build_websocket_url(exposed_thing_01, ws_server, ws_port)
    url_thing_02 = build_websocket_url(exposed_thing_02, ws_server, ws_port)

    return {
        "exposed_thing_01": exposed_thing_01,
        "exposed_thing_02": exposed_thing_02,
        "prop_init_01": prop_init_01,
        "prop_init_02": prop_init_02,
        "prop_init_03": prop_init_03,
        "event_init_01": event_init_01,
        "action_init_01": action_init_01,
        "ws_server": ws_server,
        "url_thing_01": url_thing_01,
        "url_thing_02": url_thing_02,
        "ws_port": ws_port
    }


@pytest.mark.flaky(reruns=5)
def test_thing_not_found():
    """The socket is automatically closed when connecting to an unknown thing."""

    ws_fixtures = build_websocket_server()
    ws_port = ws_fixtures.pop("ws_port")

    @tornado.gen.coroutine
    def test_coroutine():
        url_unknown = "ws://localhost:{}/{}".format(ws_port, uuid.uuid4().hex)
        conn = yield tornado.websocket.websocket_connect(url_unknown)
        msg = yield conn.read_message()

        assert msg is None

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_read_property():
    """Properties can be retrieved using Websockets."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")
    url_thing_02 = ws_fixtures.pop("url_thing_02")
    prop_init_01 = ws_fixtures.pop("prop_init_01")
    prop_init_02 = ws_fixtures.pop("prop_init_02")
    prop_init_03 = ws_fixtures.pop("prop_init_03")

    @tornado.gen.coroutine
    def test_coroutine():
        conns = yield [
            tornado.websocket.websocket_connect(url_thing_01),
            tornado.websocket.websocket_connect(url_thing_02)
        ]

        request_id_01 = Faker().pyint()
        request_id_02 = Faker().pyint()
        request_id_03 = Faker().pyint()

        ws_request_prop_01 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": prop_init_01.name},
            msg_id=request_id_01)

        ws_request_prop_02 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": prop_init_02.name},
            msg_id=request_id_02)

        ws_request_prop_03 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": prop_init_03.name},
            msg_id=request_id_03)

        conns[0].write_message(ws_request_prop_01.to_json())
        conns[0].write_message(ws_request_prop_02.to_json())
        conns[1].write_message(ws_request_prop_03.to_json())

        raw_resp_01 = yield conns[0].read_message()
        raw_resp_02 = yield conns[0].read_message()
        raw_resp_03 = yield conns[1].read_message()

        ws_resp_01 = WebsocketMessageResponse.from_raw(raw_resp_01)
        ws_resp_02 = WebsocketMessageResponse.from_raw(raw_resp_02)
        ws_resp_03 = WebsocketMessageResponse.from_raw(raw_resp_03)

        prop_init_map = {
            request_id_01: prop_init_01,
            request_id_02: prop_init_02,
            request_id_03: prop_init_03
        }

        assert ws_resp_01.result == prop_init_map[ws_resp_01.id].value
        assert ws_resp_02.result == prop_init_map[ws_resp_02.id].value
        assert ws_resp_03.result == prop_init_map[ws_resp_03.id].value

        yield conns[0].close()
        yield conns[1].close()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_write_property():
    """Properties can be updated using Websockets."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")
    prop_init_01 = ws_fixtures.pop("prop_init_01")
    exposed_thing_01 = ws_fixtures.pop("exposed_thing_01")

    @tornado.gen.coroutine
    def test_coroutine():
        conn = yield tornado.websocket.websocket_connect(url_thing_01)

        updated_value = Faker().pystr()
        prop_name = prop_init_01.name
        msg_id = uuid.uuid4().hex

        ws_request = WebsocketMessageRequest(
            method=WebsocketMethods.WRITE_PROPERTY,
            params={"name": prop_name, "value": updated_value},
            msg_id=msg_id)

        value = yield exposed_thing_01.read_property(prop_name)

        assert value != updated_value

        conn.write_message(ws_request.to_json())
        raw_response = yield conn.read_message()
        ws_response = WebsocketMessageResponse.from_raw(raw_response)

        assert ws_response.id == msg_id

        value = yield exposed_thing_01.read_property(prop_name)

        assert value == updated_value

        ws_request_err = WebsocketMessageRequest(
            method=WebsocketMethods.WRITE_PROPERTY,
            params={"name": prop_name + Faker().pystr(), "value": updated_value},
            msg_id=msg_id)

        conn.write_message(ws_request_err.to_json())
        raw_error = yield conn.read_message()
        ws_error = WebsocketMessageError.from_raw(raw_error)

        assert ws_error.code

        yield conn.close()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_invoke_action():
    """Actions can be invoked using Websockets."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")
    action_init_01 = ws_fixtures.pop("action_init_01")
    exposed_thing_01 = ws_fixtures.pop("exposed_thing_01")

    @tornado.gen.coroutine
    def test_coroutine():
        conn = yield tornado.websocket.websocket_connect(url_thing_01)

        input_val = Faker().pystr()
        action_name = action_init_01.name

        expected_out = yield exposed_thing_01.invoke_action(action_name, input_val)

        msg_id = Faker().pyint()

        msg_invoke_req = WebsocketMessageRequest(
            method=WebsocketMethods.INVOKE_ACTION,
            params={"name": action_name, "parameters": {"val": input_val}},
            msg_id=msg_id)

        conn.write_message(msg_invoke_req.to_json())

        msg_invoke_resp_raw = yield conn.read_message()
        msg_invoke_resp = WebsocketMessageResponse.from_raw(msg_invoke_resp_raw)

        assert msg_invoke_resp.id == msg_id
        assert msg_invoke_resp.result == expected_out

        yield conn.close()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_property_change():
    """Property changes can be observed using Websockets."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")
    prop_init_01 = ws_fixtures.pop("prop_init_01")
    exposed_thing_01 = ws_fixtures.pop("exposed_thing_01")

    @tornado.gen.coroutine
    def test_coroutine():
        observe_msg_id = Faker().pyint()
        prop_name = prop_init_01.name

        updated_val_01 = Faker().pystr()
        updated_val_02 = Faker().pystr()
        updated_val_03 = Faker().pystr()

        conn = yield tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": prop_name},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        def assert_emitted(the_msg_raw, the_expected_val):
            msg_emitted = WebsocketMessageEmittedItem.from_raw(the_msg_raw)

            assert msg_emitted.subscription_id == subscription_id
            assert msg_emitted.data["name"] == prop_name
            assert msg_emitted.data["value"] == the_expected_val

        yield exposed_thing_01.write_property(prop_name, updated_val_01)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_01)

        yield exposed_thing_01.write_property(prop_name, updated_val_02)
        yield exposed_thing_01.write_property(prop_name, updated_val_03)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_02)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_03)

        yield conn.close()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_undefined_property_change():
    """Observing an undefined property results in a subscription error message."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")

    @tornado.gen.coroutine
    def test_coroutine():
        observe_msg_id = Faker().pyint()
        prop_name_err = uuid.uuid4().hex

        conn = yield tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": prop_name_err},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        msg_observe_err_raw = yield conn.read_message()
        msg_observe_err = WebsocketMessageError.from_raw(msg_observe_err_raw)

        assert msg_observe_err.code == WebsocketErrors.SUBSCRIPTION_ERROR
        assert msg_observe_err.data["subscription"] == msg_observe_resp.result

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_event():
    """Events can be observed using Websockets."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")
    event_init_01 = ws_fixtures.pop("event_init_01")
    exposed_thing_01 = ws_fixtures.pop("exposed_thing_01")

    @tornado.gen.coroutine
    def test_coroutine():
        observe_msg_id = Faker().pyint()
        event_name = event_init_01.name
        payload_01 = Faker().pydict(10, True, str, float)
        payload_02 = Faker().pydict(10, True, str, float)
        payload_03 = Faker().pydict(10, True, int)

        conn = yield tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_EVENT,
            params={"name": event_name},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        def assert_emitted(the_msg_raw, the_expected_payload):
            msg_emitted = WebsocketMessageEmittedItem.from_raw(the_msg_raw)

            assert msg_emitted.subscription_id == subscription_id
            assert msg_emitted.data == the_expected_payload

        exposed_thing_01.emit_event(event_name, payload_01)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, payload_01)

        exposed_thing_01.emit_event(event_name, payload_02)
        exposed_thing_01.emit_event(event_name, payload_03)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, payload_02)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, payload_03)

        yield conn.close()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_undefined_event():
    """Observing an undefined event results in a subscription error message."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")

    @tornado.gen.coroutine
    def test_coroutine():
        observe_msg_id = Faker().pyint()
        event_name_err = Faker().pystr()

        conn = yield tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_EVENT,
            params={"name": event_name_err},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        msg_observe_err_raw = yield conn.read_message()
        msg_observe_err = WebsocketMessageError.from_raw(msg_observe_err_raw)

        assert msg_observe_err.code == WebsocketErrors.SUBSCRIPTION_ERROR
        assert msg_observe_err.data["subscription"] == msg_observe_resp.result

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_on_td_change():
    """Thing description changes can be observed using Websockets."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")
    exposed_thing_01 = ws_fixtures.pop("exposed_thing_01")

    @tornado.gen.coroutine
    def test_coroutine():
        td_change_msg_id = Faker().pyint()

        conn = yield tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_TD_CHANGE,
            params={},
            msg_id=td_change_msg_id)

        conn.write_message(msg_observe_req.to_json())

        td_change_resp_raw = yield conn.read_message()
        td_change_resp = WebsocketMessageResponse.from_raw(td_change_resp_raw)

        assert td_change_resp.id == td_change_msg_id

        new_prop_init = ThingPropertyInit(
            name=uuid.uuid4().hex,
            value=Faker().sentence(),
            data_type={"type": "string"},
            writable=False,
            observable=True)

        exposed_thing_01.add_property(new_prop_init)

        msg_emitted_raw = yield conn.read_message()
        msg_emitted = WebsocketMessageEmittedItem.from_raw(msg_emitted_raw)

        assert msg_emitted.data.get("name") == new_prop_init.name
        assert msg_emitted.data.get("data", {}).get("name") == new_prop_init.name
        assert msg_emitted.data.get("data", {}).get("value") == new_prop_init.value
        assert msg_emitted.data.get("data", {}).get("writable") == new_prop_init.writable
        assert msg_emitted.data.get("data", {}).get("observable") == new_prop_init.observable

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_dispose():
    """Observable subscriptions can be disposed using Websockets."""

    ws_fixtures = build_websocket_server()
    url_thing_01 = ws_fixtures.pop("url_thing_01")
    prop_init_01 = ws_fixtures.pop("prop_init_01")
    exposed_thing_01 = ws_fixtures.pop("exposed_thing_01")

    @tornado.gen.coroutine
    def test_coroutine():
        observe_msg_id = Faker().pyint()
        dispose_msg_id = Faker().pyint()
        prop_name = prop_init_01.name

        conn = yield tornado.websocket.websocket_connect(url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": prop_name},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        yield exposed_thing_01.write_property(prop_name, Faker().sentence())

        msg_emitted_raw = yield conn.read_message()
        msg_emitted = WebsocketMessageEmittedItem.from_raw(msg_emitted_raw)

        assert msg_emitted.subscription_id == subscription_id

        msg_dispose_req = WebsocketMessageRequest(
            method=WebsocketMethods.DISPOSE,
            params={"subscription": subscription_id},
            msg_id=dispose_msg_id)

        conn.write_message(msg_dispose_req.to_json())

        msg_dispose_resp_raw = yield conn.read_message()
        msg_dispose_resp = WebsocketMessageResponse.from_raw(msg_dispose_resp_raw)

        assert msg_dispose_resp.result == subscription_id

        conn.write_message(msg_dispose_req.to_json())

        msg_dispose_resp_02_raw = yield conn.read_message()
        msg_dispose_resp_02 = WebsocketMessageResponse.from_raw(msg_dispose_resp_02_raw)

        assert not msg_dispose_resp_02.result

        yield exposed_thing_01.write_property(prop_name, Faker().pystr())
        yield exposed_thing_01.write_property(prop_name, Faker().pystr())

        with pytest.raises(tornado.gen.TimeoutError):
            yield tornado.gen.with_timeout(
                timeout=datetime.timedelta(milliseconds=200),
                future=conn.read_message())

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)