#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the Websocket protocol.
"""

import uuid

import tornado.gen
import tornado.websocket
from six.moves import urllib

from wotpy.protocols.client import BaseProtocolClient, ProtocolClientException
from wotpy.protocols.enums import Protocols, ProtocolSchemes
from wotpy.protocols.ws.enums import WebsocketMethods
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageResponse, \
    WebsocketMessageError, \
    WebsocketMessageException


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

    @tornado.gen.coroutine
    def _wait_for_response(self, ws_conn, msg_id):
        """Waits for the WebSocket response message that matches the given ID."""

        def parse_response(raw):
            """Attempts to parse the raw message as a WS response."""

            try:
                resp = WebsocketMessageResponse.from_raw(raw)

                if resp.id == msg_id:
                    raise tornado.gen.Return(resp.result)
            except WebsocketMessageException:
                pass

        def parse_error(raw):
            """Attempts to parse the raw message as a WS error."""

            try:
                err = WebsocketMessageError.from_raw(raw)

                if err.id == msg_id:
                    raise Exception(err.message)
            except WebsocketMessageException:
                pass

        while True:
            raw_res = yield ws_conn.read_message()
            parse_response(raw_res)
            parse_error(raw_res)

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
        Returns an Observable"""

        raise NotImplementedError()

    def on_td_change(self, td):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError()
