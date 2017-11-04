#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime

# noinspection PyPackageRequirements
import pytest
import tornado.gen
import tornado.testing
import tornado.websocket
# noinspection PyPackageRequirements
from faker import Faker

from wotpy.protocols.ws.enums import WebsocketMethods, WebsocketErrors
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageResponse, \
    WebsocketMessageError, \
    WebsocketMessageEmittedItem
from wotpy.protocols.ws.server import WebsocketServer
from wotpy.wot.dictionaries import ThingPropertyInit
from wotpy.wot.enums import RequestType
from wotpy.wot.exposed import ExposedThing


class TestWebsocketServer(tornado.testing.AsyncHTTPTestCase):
    """Test case for the WoT Websockets server."""

    # noinspection PyAttributeOutsideInit
    def setUp(self):
        self.fake = Faker()

        # ToDo: Set the Servient
        self.exposed_thing_01 = ExposedThing.from_name(
            servient=None,
            name=self.fake.user_name())

        # ToDo: Set the Servient
        self.exposed_thing_02 = ExposedThing.from_name(
            servient=None,
            name=self.fake.user_name())

        self.prop_init_01 = ThingPropertyInit(
            name=self.fake.user_name(),
            value=self.fake.pystr(),
            description={"type": "string"})

        self.prop_init_02 = ThingPropertyInit(
            name=self.fake.user_name(),
            value=self.fake.pystr(),
            description={"type": "string"})

        self.prop_init_03 = ThingPropertyInit(
            name=self.fake.user_name(),
            value=self.fake.pystr(),
            description={"type": "string"})

        self.exposed_thing_01.add_property(self.prop_init_01)
        self.exposed_thing_01.add_property(self.prop_init_02)
        self.exposed_thing_02.add_property(self.prop_init_03)

        self.ws_server = WebsocketServer()
        self.ws_server.add_exposed_thing(self.exposed_thing_01)
        self.ws_server.add_exposed_thing(self.exposed_thing_02)

        super(TestWebsocketServer, self).setUp()

        self.url_thing_01 = self._build_root_url(self.exposed_thing_01)
        self.url_thing_02 = self._build_root_url(self.exposed_thing_02)

    def get_app(self):
        """Should be overridden by subclasses to return a tornado.web.Application
        or other HTTPServer callback. Returns a Websockets WoT server Application."""

        return self.ws_server.build_app()

    def _build_root_url(self, exposed_thing):
        """Returns the WS connection URL for the given ExposedThing."""

        return "ws://localhost:{}{}".format(
            self.get_http_port(),
            WebsocketServer.path_for_exposed_thing(exposed_thing))

    @tornado.testing.gen_test
    def test_get_property(self):
        """Properties can be retrieved using Websockets."""

        conns = yield [
            tornado.websocket.websocket_connect(self.url_thing_01),
            tornado.websocket.websocket_connect(self.url_thing_02)
        ]

        request_id_01 = self.fake.pyint()
        request_id_02 = self.fake.pyint()
        request_id_03 = self.fake.pyint()

        ws_request_prop_01 = WebsocketMessageRequest(
            method=WebsocketMethods.GET_PROPERTY,
            params={"name": self.prop_init_01.name},
            msg_id=request_id_01)

        ws_request_prop_02 = WebsocketMessageRequest(
            method=WebsocketMethods.GET_PROPERTY,
            params={"name": self.prop_init_02.name},
            msg_id=request_id_02)

        ws_request_prop_03 = WebsocketMessageRequest(
            method=WebsocketMethods.GET_PROPERTY,
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
    def test_set_property(self):
        """Properties can be updated using Websockets."""

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

        updated_value = self.fake.pystr()
        prop_name = self.prop_init_01.name
        msg_id = self.fake.pyint()

        ws_request = WebsocketMessageRequest(
            method=WebsocketMethods.SET_PROPERTY,
            params={"name": prop_name, "value": updated_value},
            msg_id=msg_id)

        assert self.exposed_thing_01.get_property(prop_name).result() != updated_value

        conn.write_message(ws_request.to_json())
        raw_response = yield conn.read_message()
        ws_response = WebsocketMessageResponse.from_raw(raw_response)

        assert ws_response.id == msg_id
        assert self.exposed_thing_01.get_property(prop_name).result() == updated_value

        ws_request_err = WebsocketMessageRequest(
            method=WebsocketMethods.SET_PROPERTY,
            params={"name": prop_name + self.fake.pystr(), "value": updated_value},
            msg_id=msg_id)

        conn.write_message(ws_request_err.to_json())
        raw_error = yield conn.read_message()
        ws_error = WebsocketMessageError.from_raw(raw_error)

        assert ws_error.code

    @tornado.testing.gen_test
    def test_observe_property(self):
        """Properties can be observed using Websockets."""

        observe_msg_id = self.fake.pyint()
        prop_name = self.prop_init_01.name

        updated_val_01 = self.fake.pystr()
        updated_val_02 = self.fake.pystr()
        updated_val_03 = self.fake.pystr()

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.OBSERVE,
            params={"name": prop_name, "request_type": RequestType.PROPERTY},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        def _assert_emitted(expected_val):
            msg_emitted_raw = yield conn.read_message()
            msg_emitted = WebsocketMessageEmittedItem.from_raw(msg_emitted_raw)

            assert msg_emitted.subscription_id == subscription_id
            assert msg_emitted.data["name"] == prop_name
            assert msg_emitted.data["value"] == expected_val

        assert self.exposed_thing_01.set_property(prop_name, updated_val_01).done()

        _assert_emitted(updated_val_01)

        assert self.exposed_thing_01.set_property(prop_name, updated_val_02).done()
        assert self.exposed_thing_01.set_property(prop_name, updated_val_03).done()

        _assert_emitted(updated_val_02)
        _assert_emitted(updated_val_03)

    @tornado.testing.gen_test
    def test_observe_not_found_error(self):
        """Observing an unexisting interaction results in a subscription error message."""

        observe_msg_id = self.fake.pyint()
        prop_name_err = self.fake.pystr()

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.OBSERVE,
            params={"name": prop_name_err, "request_type": RequestType.PROPERTY},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        msg_observe_err_raw = yield conn.read_message()
        msg_observe_err = WebsocketMessageError.from_raw(msg_observe_err_raw)

        assert msg_observe_err.code == WebsocketErrors.SUBSCRIPTION_ERROR
        assert msg_observe_err.data["subscription"] == msg_observe_resp.result

    @tornado.testing.gen_test
    def test_observe_dispose(self):
        """Observable subscriptions can be disposed using Websockets."""

        observe_msg_id = self.fake.pyint()
        dispose_msg_id = self.fake.pyint()
        prop_name = self.prop_init_01.name

        conn = yield tornado.websocket.websocket_connect(self.url_thing_01)

        msg_observe_req = WebsocketMessageRequest(
            method=WebsocketMethods.OBSERVE,
            params={"name": prop_name, "request_type": RequestType.PROPERTY},
            msg_id=observe_msg_id)

        conn.write_message(msg_observe_req.to_json())

        msg_observe_resp_raw = yield conn.read_message()
        msg_observe_resp = WebsocketMessageResponse.from_raw(msg_observe_resp_raw)

        assert msg_observe_resp.id == observe_msg_id

        subscription_id = msg_observe_resp.result

        assert self.exposed_thing_01.set_property(prop_name, self.fake.pystr()).done()

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

        assert self.exposed_thing_01.set_property(prop_name, self.fake.pystr()).done()
        assert self.exposed_thing_01.set_property(prop_name, self.fake.pystr()).done()

        with pytest.raises(tornado.gen.TimeoutError):
            yield tornado.gen.with_timeout(
                timeout=datetime.timedelta(milliseconds=200),
                future=conn.read_message())
