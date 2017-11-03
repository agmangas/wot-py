#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tornado import websocket, gen
from jsonschema import validate, ValidationError

from wotpy.protocols.ws.enums import WebsocketMethods, WebsocketErrors
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageException, \
    WebsocketMessageError, \
    WebsocketMessageResponse
from wotpy.protocols.ws.schemas import \
    SCHEMA_PARAMS_GET_PROPERTY, \
    SCHEMA_PARAMS_SET_PROPERTY


# noinspection PyAbstractClass
class WebsocketHandler(websocket.WebSocketHandler):
    """Tornado handler for Websocket messages."""

    def __init__(self, *args, **kwargs):
        assert "exposed_thing" in kwargs, "Argument 'exposed_thing' required"
        self._exposed_thing = kwargs.pop("exposed_thing")
        super(WebsocketHandler, self).__init__(*args, **kwargs)

    def open(self):
        """"""

        pass

    def _write_error(self, message, code, res_id=None):
        """"""

        err = WebsocketMessageError(message=message, code=code, res_id=res_id)
        self.write_message(err.to_json())

    @gen.coroutine
    def _handle_get_property(self, req):
        """"""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_GET_PROPERTY)
        except ValidationError as ex:
            self._write_error(ex.message, WebsocketErrors.INVALID_METHOD_PARAMS, req.req_id)
            return

        try:
            prop_value = yield self._exposed_thing.get_property(name=params["name"])
        except Exception as ex:
            self._write_error(ex.message, WebsocketErrors.INTERNAL_ERROR, req.req_id)
            return

        res = WebsocketMessageResponse(result=prop_value, res_id=req.req_id)
        self.write_message(res.to_json())

    @gen.coroutine
    def _handle_set_property(self, req):
        """"""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_SET_PROPERTY)
        except ValidationError as ex:
            self._write_error(ex.message, WebsocketErrors.INVALID_METHOD_PARAMS, req.req_id)
            return

        try:
            yield self._exposed_thing.set_property(name=params["name"], value=params["value"])
        except Exception as ex:
            self._write_error(ex.message, WebsocketErrors.INTERNAL_ERROR, req.req_id)
            return

        res = WebsocketMessageResponse(result=None, res_id=req.req_id)
        self.write_message(res.to_json())

    @gen.coroutine
    def _handle(self, req):
        """"""

        handler_map = {
            WebsocketMethods.GET_PROPERTY: self._handle_get_property,
            WebsocketMethods.SET_PROPERTY: self._handle_set_property
        }

        if req.method not in handler_map:
            self._write_error("Unimplemented method", WebsocketErrors.INTERNAL_ERROR, req.req_id)
            return

        handler = handler_map[req.method]
        yield handler(req)

    @gen.coroutine
    def on_message(self, message):
        """"""

        try:
            req = WebsocketMessageRequest.from_raw(message)
            yield self._handle(req)
        except WebsocketMessageException as ex:
            self._write_error(ex.message, WebsocketErrors.INTERNAL_ERROR)

    def on_close(self):
        """"""

        pass
