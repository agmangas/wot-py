#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re
import time

# noinspection PyPackageRequirements
import pytest
import tornado.gen
import tornado.testing
import tornado.websocket
# noinspection PyCompatibility
from concurrent.futures import ThreadPoolExecutor
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
from wotpy.wot.dictionaries import ThingPropertyInit, ThingEventInit, ThingActionInit
from wotpy.wot.exposed import ExposedThing
from wotpy.wot.servient import Servient


class TestWebsocketHandler(tornado.testing.AsyncHTTPTestCase):
    """Test case for the WoT WebSockets server handler."""

    # noinspection PyAttributeOutsideInit
    def setUp(self):
        self.fake = Faker()

        servient = Servient()

        thing_01_name = self.fake.pystr()
        thing_02_name = self.fake.pystr()

        self.exposed_thing_01 = ExposedThing.from_name(
            servient=servient,
            name=thing_01_name)

        self.exposed_thing_02 = ExposedThing.from_name(
            servient=servient,
            name=thing_02_name)

        self.prop_init_01 = ThingPropertyInit(
            name=self.fake.user_name(),
            value=self.fake.pystr(),
            data_type={"type": "string"})

        self.prop_init_02 = ThingPropertyInit(
            name=self.fake.user_name(),
            value=self.fake.pystr(),
            data_type={"type": "string"})

        self.prop_init_03 = ThingPropertyInit(
            name=self.fake.user_name(),
            value=self.fake.pystr(),
            data_type={"type": "string"})

        self.event_init_01 = ThingEventInit(
            name=self.fake.user_name(),
            data_description={"type": "object"})

        self.action_init_01 = ThingActionInit(
            name=self.fake.user_name(),
            input_data_description={"type": "string"},
            output_data_description={"type": "string"})

        executor = ThreadPoolExecutor(max_workers=1)

        def async_lower(val):
            return executor.submit(lambda x: time.sleep(0.05) or x.lower(), val)

        self.exposed_thing_01.add_property(self.prop_init_01)
        self.exposed_thing_01.add_property(self.prop_init_02)
        self.exposed_thing_01.add_event(self.event_init_01)
        self.exposed_thing_01.add_action(self.action_init_01)
        self.exposed_thing_01.set_action_handler(async_lower, self.action_init_01.name)

        self.exposed_thing_02.add_property(self.prop_init_03)

        self.ws_server = WebsocketServer()
        self.ws_server.add_exposed_thing(self.exposed_thing_01)
        self.ws_server.add_exposed_thing(self.exposed_thing_02)

        super(TestWebsocketHandler, self).setUp()

        self.url_thing_01 = self._build_root_url(self.exposed_thing_01)
        self.url_thing_02 = self._build_root_url(self.exposed_thing_02)

    def get_app(self):
        """Should be overridden by subclasses to return a tornado.web.Application
        or other HTTPServer callback. Returns a Websockets WoT server Application."""

        return self.ws_server.app

    def _build_root_url(self, exposed_thing):
        """Returns the WS connection URL for the given ExposedThing."""

        base_url = self.ws_server.get_thing_base_url(hostname="localhost", exposed_thing=exposed_thing)
        parsed_url = urlparse(base_url)
        server_port = self.get_http_port()
        test_netloc = re.sub(r':(\d+)$', ':{}'.format(server_port), parsed_url.netloc)

        test_url_parts = list(parsed_url)
        test_url_parts[1] = test_netloc

        return urlunparse(test_url_parts)

    @tornado.testing.gen_test
    def test_not_found_error(self):
        """The socket is automatically closed when connecting to an unknown thing."""

        url_unknown = "ws://localhost:{}/{}".format(self.get_http_port(), self.fake.pystr())
        conn = yield tornado.websocket.websocket_connect(url_unknown)
        msg = yield conn.read_message()

        assert msg is None

    @tornado.testing.gen_test
    def test_read_property(self):
        """Properties can be retrieved using Websockets."""

        conns = yield [
            tornado.websocket.websocket_connect(self.url_thing_01),
            tornado.websocket.websocket_connect(self.url_thing_02)
        ]

        request_id_01 = self.fake.pyint()
        request_id_02 = self.fake.pyint()
        request_id_03 = self.fake.pyint()

        ws_request_prop_01 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": self.prop_init_01.name},
            msg_id=request_id_01)

        ws_request_prop_02 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": self.prop_init_02.name},
            msg_id=request_id_02)

        ws_request_prop_03 = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": self.prop_init_03.name},
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
            request_id_01: self.prop_init_01,
            request_id_02: self.prop_init_02,
            request_id_03: self.prop_init_03
        }

        assert ws_resp_01.result == prop_init_map[ws_resp_01.id].value
        assert ws_resp_02.result == prop_init_map[ws_resp_02.id].value
        assert ws_resp_03.result == prop_init_map[ws_resp_03.id].value

        yield conns[0].close()
        yield conns[1].close()

    @tornado.testing.gen_test
    def test_write_property(self):
        """Properties can be updated using Websockets."""

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

        updated_value = self.fake.pystr()
        prop_name = self.prop_init_01.name
        msg_id = self.fake.pyint()

        ws_request = WebsocketMessageRequest(
            method=WebsocketMethods.WRITE_PROPERTY,
            params={"name": prop_name, "value": updated_value},
            msg_id=msg_id)

        assert self.exposed_thing_01.read_property(prop_name).result() != updated_value

        conn.write_message(ws_request.to_json())
        raw_response = yield conn.read_message()
        ws_response = WebsocketMessageResponse.from_raw(raw_response)

        assert ws_response.id == msg_id
        assert self.exposed_thing_01.read_property(prop_name).result() == updated_value

        ws_request_err = WebsocketMessageRequest(
            method=WebsocketMethods.WRITE_PROPERTY,
            params={"name": prop_name + self.fake.pystr(), "value": updated_value},
            msg_id=msg_id)

        conn.write_message(ws_request_err.to_json())
        raw_error = yield conn.read_message()
        ws_error = WebsocketMessageError.from_raw(raw_error)

        assert ws_error.code

        yield conn.close()

    @tornado.testing.gen_test
    def test_invoke_action(self):
        """Actions can be invoked using Websockets."""

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

        input_val = self.fake.pystr()
        action_name = self.action_init_01.name
        expected_out = self.exposed_thing_01.invoke_action(action_name, input_val).result()
        msg_id = self.fake.pyint()

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

    @tornado.testing.gen_test
    def test_on_property_change(self):
        """Property changes can be observed using Websockets."""

        observe_msg_id = self.fake.pyint()
        prop_name = self.prop_init_01.name

        updated_val_01 = self.fake.pystr()
        updated_val_02 = self.fake.pystr()
        updated_val_03 = self.fake.pystr()

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

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

        assert self.exposed_thing_01.write_property(prop_name, updated_val_01).done()

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_01)

        assert self.exposed_thing_01.write_property(prop_name, updated_val_02).done()
        assert self.exposed_thing_01.write_property(prop_name, updated_val_03).done()

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_02)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, updated_val_03)

        yield conn.close()

    @tornado.testing.gen_test
    def test_on_undefined_property_change(self):
        """Observing an undefined property results in a subscription error message."""

        observe_msg_id = self.fake.pyint()
        prop_name_err = self.fake.pystr()

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

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

    @tornado.testing.gen_test
    def test_on_event(self):
        """Events can be observed using Websockets."""

        observe_msg_id = self.fake.pyint()
        event_name = self.event_init_01.name
        payload_01 = self.fake.pydict(10, True, str, float)
        payload_02 = self.fake.pydict(10, True, str, float)
        payload_03 = self.fake.pydict(10, True, int)

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

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

        self.exposed_thing_01.emit_event(event_name, payload_01)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, payload_01)

        self.exposed_thing_01.emit_event(event_name, payload_02)
        self.exposed_thing_01.emit_event(event_name, payload_03)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, payload_02)

        msg_emitted_raw = yield conn.read_message()
        assert_emitted(msg_emitted_raw, payload_03)

        yield conn.close()

    @tornado.testing.gen_test
    def test_on_undefined_event(self):
        """Observing an undefined event results in a subscription error message."""

        observe_msg_id = self.fake.pyint()
        event_name_err = self.fake.pystr()

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

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

    @tornado.testing.gen_test
    def test_on_td_change(self):
        """Thing description changes can be observed using Websockets."""

        td_change_msg_id = self.fake.pyint()

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_TD_CHANGE,
            params={},
            msg_id=td_change_msg_id)

        conn.write_message(msg_observe_req.to_json())

        td_change_resp_raw = yield conn.read_message()
        td_change_resp = WebsocketMessageResponse.from_raw(td_change_resp_raw)

        assert td_change_resp.id == td_change_msg_id

        new_prop_init = ThingPropertyInit(
            name=self.fake.user_name(),
            value=self.fake.pystr(),
            data_type={"type": "string"},
            writable=False,
            observable=True)

        self.exposed_thing_01.add_property(new_prop_init)

        msg_emitted_raw = yield conn.read_message()
        msg_emitted = WebsocketMessageEmittedItem.from_raw(msg_emitted_raw)

        assert msg_emitted.data.get("name") == new_prop_init.name
        assert msg_emitted.data.get("data", {}).get("name") == new_prop_init.name
        assert msg_emitted.data.get("data", {}).get("value") == new_prop_init.value
        assert msg_emitted.data.get("data", {}).get("writable") == new_prop_init.writable
        assert msg_emitted.data.get("data", {}).get("observable") == new_prop_init.observable

    @tornado.testing.gen_test
    def test_dispose(self):
        """Observable subscriptions can be disposed using Websockets."""

        observe_msg_id = self.fake.pyint()
        dispose_msg_id = self.fake.pyint()
        prop_name = self.prop_init_01.name

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": prop_name},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        assert self.exposed_thing_01.write_property(prop_name, self.fake.pystr()).done()

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

        assert self.exposed_thing_01.write_property(prop_name, self.fake.pystr()).done()
        assert self.exposed_thing_01.write_property(prop_name, self.fake.pystr()).done()

        with pytest.raises(tornado.gen.TimeoutError):
            yield tornado.gen.with_timeout(
                timeout=datetime.timedelta(milliseconds=200),
                future=conn.read_message())
