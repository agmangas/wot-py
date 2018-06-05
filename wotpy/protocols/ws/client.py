#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the Websocket protocol.
"""

import uuid

import tornado.gen
import tornado.websocket
from rx import Observable
from six.moves import urllib
from tornado.concurrent import Future

from wotpy.protocols.client import BaseProtocolClient, ProtocolClientException
from wotpy.protocols.enums import Protocols, ProtocolSchemes
from wotpy.protocols.ws.enums import WebsocketMethods
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageResponse, \
    WebsocketMessageEmittedItem, \
    WebsocketMessageError, \
    WebsocketMessageException
from wotpy.wot.dictionaries import PropertyChangeEventInit
from wotpy.wot.events import PropertyChangeEmittedEvent


class WebsocketClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the Websocket protocol."""

    @classmethod
    def _pick_form(cls, td, forms):
        """Picks the Form that will be used to connect to the remote Thing."""

        def is_websocket(form):
            """Returns True if the given Form belongs to the Websocket binding."""

            resolved_url = td.resolve_form_uri(form)

            if not resolved_url:
                return False

            valid_schemes = [ProtocolSchemes.scheme_for_protocol(Protocols.WEBSOCKETS)]

            return urllib.parse.urlparse(resolved_url).scheme in valid_schemes

        forms_ws = [item for item in forms if is_websocket(item)]

        if not len(forms_ws):
            return None

        return forms_ws[0]

    @classmethod
    def _parse_response(cls, raw_msg, msg_id):
        """Returns a parsed WS response message instance if
        the raw message format is valid and has the given ID."""

        try:
            msg = WebsocketMessageResponse.from_raw(raw_msg)

            if msg.id == msg_id:
                return msg
        except WebsocketMessageException:
            pass

        try:
            err = WebsocketMessageError.from_raw(raw_msg)

            if err.id == msg_id:
                raise Exception(err.message)
        except WebsocketMessageException:
            pass

        return None

    @classmethod
    def _parse_emitted_item(cls, raw_msg, sub_id):
        """Returns a parsed WS emitted item message instance if
        the raw message format is valid and has the given ID."""

        try:
            msg = WebsocketMessageEmittedItem.from_raw(raw_msg)

            if msg.subscription_id == sub_id:
                return msg
        except WebsocketMessageException:
            pass

        try:
            err = WebsocketMessageError.from_raw(raw_msg)
            err_sub_id = err.data is not None and err.data.get("subscription")

            if err_sub_id == sub_id:
                raise Exception(err.message)
        except WebsocketMessageException:
            pass

        return None

    @tornado.gen.coroutine
    def _wait_for_response(self, ws_conn, msg_id):
        """Waits for the WebSocket response message that matches the given ID."""

        while True:
            raw_res = yield ws_conn.read_message()

            if raw_res is None:
                raise Exception("WS connection closed")

            msg_res = self._parse_response(raw_res, msg_id)

            if msg_res is not None:
                raise tornado.gen.Return(msg_res.result)

    @tornado.gen.coroutine
    def _send_websocket_message(self, ws_url, msg_req):
        """Sends a WebSocket request message, waits for the response and returns the result."""

        ws_conn = yield tornado.websocket.websocket_connect(ws_url)
        ws_conn.write_message(msg_req.to_json())

        result = yield self._wait_for_response(ws_conn, msg_req.id)

        yield ws_conn.close()

        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def invoke_action(self, td, name, *args, **kwargs):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        form = self._pick_form(td, td.get_action_forms(name))

        if not form:
            raise ProtocolClientException()

        ws_url = td.resolve_form_uri(form)

        msg_req = WebsocketMessageRequest(
            method=WebsocketMethods.INVOKE_ACTION,
            params={"name": name, "parameters": kwargs},
            msg_id=uuid.uuid4().hex)

        result = yield self._send_websocket_message(ws_url, msg_req)

        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        form = self._pick_form(td, td.get_property_forms(name))

        if not form:
            raise ProtocolClientException()

        ws_url = td.resolve_form_uri(form)

        msg_req = WebsocketMessageRequest(
            method=WebsocketMethods.WRITE_PROPERTY,
            params={"name": name, "value": value},
            msg_id=uuid.uuid4().hex)

        result = yield self._send_websocket_message(ws_url, msg_req)

        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def read_property(self, td, name):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        form = self._pick_form(td, td.get_property_forms(name))

        if not form:
            raise ProtocolClientException()

        ws_url = td.resolve_form_uri(form)

        msg_req = WebsocketMessageRequest(
            method=WebsocketMethods.READ_PROPERTY,
            params={"name": name},
            msg_id=uuid.uuid4().hex)

        result = yield self._send_websocket_message(ws_url, msg_req)

        raise tornado.gen.Return(result)

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError()

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable."""

        form = self._pick_form(td, td.get_property_forms(name))

        if not form:
            raise ProtocolClientException()

        ws_url = td.resolve_form_uri(form)

        msg_req = WebsocketMessageRequest(
            method=WebsocketMethods.ON_PROPERTY_CHANGE,
            params={"name": name},
            msg_id=uuid.uuid4().hex)

        def subscribe(observer):
            """Connect to the WS server and start passing the received events to the Observer."""

            future_sub_id = Future()
            future_ws_conn = Future()

            def on_error(ex):
                observer.on_error(ex)
                observer.on_complete()

            def on_next_event(raw_msg):
                sub_id = future_sub_id.result()

                try:
                    msg_item = self._parse_emitted_item(raw_msg, sub_id)
                except Exception as ex:
                    return on_error(ex)

                if msg_item is None:
                    return

                init = PropertyChangeEventInit(name=msg_item.data["name"], value=msg_item.data["value"])
                observer.on_next(PropertyChangeEmittedEvent(init=init))

            def parse_subscription_id(raw_msg):
                try:
                    msg_res = self._parse_response(raw_msg, msg_req.id)
                except Exception as ex:
                    return on_error(ex)

                if msg_res is None:
                    return

                sub_id = msg_res.result
                future_sub_id.set_result(sub_id)

            def on_message(raw_msg):
                if raw_msg is None:
                    return on_error(Exception("WS connection closed"))

                if future_sub_id.done():
                    on_next_event(raw_msg)
                else:
                    parse_subscription_id(raw_msg)

            def on_connect(ft):
                ws_conn = ft.result()
                future_ws_conn.set_result(ws_conn)
                ws_conn.write_message(msg_req.to_json())

            tornado.websocket.websocket_connect(ws_url, callback=on_connect, on_message_callback=on_message)

            def unsubscribe():
                if future_ws_conn.done():
                    ws_conn = future_ws_conn.result()
                    ws_conn.close()

            return unsubscribe

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_td_change(self, td):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError()
