#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

from tornado import websocket, gen
from jsonschema import validate, ValidationError
from rx.concurrency import IOLoopScheduler

from wotpy.protocols.ws.enums import WebsocketMethods, WebsocketErrors
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageException, \
    WebsocketMessageError, \
    WebsocketMessageResponse, \
    WebsocketMessageEmittedItem
from wotpy.protocols.ws.schemas import \
    SCHEMA_PARAMS_GET_PROPERTY, \
    SCHEMA_PARAMS_SET_PROPERTY, \
    SCHEMA_PARAMS_OBSERVE, \
    SCHEMA_PARAMS_DISPOSE


# noinspection PyAbstractClass
class WebsocketHandler(websocket.WebSocketHandler):
    """Tornado handler for Websocket messages."""

    def __init__(self, *args, **kwargs):
        assert "exposed_thing" in kwargs, "Argument 'exposed_thing' required"
        self._exposed_thing = kwargs.pop("exposed_thing")
        self._scheduler = IOLoopScheduler()
        self._subscriptions = {}
        super(WebsocketHandler, self).__init__(*args, **kwargs)

    def open(self):
        """"""

        pass

    def _write_error(self, message, code, msg_id=None, data=None):
        """"""

        err = WebsocketMessageError(message=message, code=code, data=data, msg_id=msg_id)
        self.write_message(err.to_json())

    def _dispose_subscription(self, subscription_id):
        """"""

        if subscription_id in self._subscriptions:
            subscription = self._subscriptions.pop(subscription_id)
            subscription.dispose()

    @gen.coroutine
    def _handle_get_property(self, req):
        """"""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_GET_PROPERTY)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        try:
            prop_value = yield self._exposed_thing.get_property(name=params["name"])
        except Exception as ex:
            self._write_error(str(ex), WebsocketErrors.INTERNAL_ERROR, msg_id=req.id)
            return

        res = WebsocketMessageResponse(result=prop_value, msg_id=req.id)
        self.write_message(res.to_json())

    @gen.coroutine
    def _handle_set_property(self, req):
        """"""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_SET_PROPERTY)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        try:
            yield self._exposed_thing.set_property(name=params["name"], value=params["value"])
        except Exception as ex:
            self._write_error(str(ex), WebsocketErrors.INTERNAL_ERROR, msg_id=req.id)
            return

        res = WebsocketMessageResponse(result=None, msg_id=req.id)
        self.write_message(res.to_json())

    @gen.coroutine
    def _handle_observe(self, req):
        """"""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_OBSERVE)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        subscription_id = str(uuid.uuid4())

        def _on_next(item):
            try:
                msg = WebsocketMessageEmittedItem(
                    subscription_id=subscription_id,
                    name=item.name,
                    data=item.data)
                self.write_message(msg.to_json())
            except WebsocketMessageError as ws_ex:
                self._dispose_subscription(subscription_id)
                data_err = {"subscription": subscription_id}
                self._write_error(str(ws_ex), WebsocketErrors.SUBSCRIPTION_ERROR, data=data_err)

        def _on_completed():
            self._dispose_subscription(subscription_id)

        def _on_error(err):
            self._dispose_subscription(subscription_id)
            data_err = {"subscription": subscription_id}
            self._write_error(str(err), WebsocketErrors.SUBSCRIPTION_ERROR, data=data_err)

        res = WebsocketMessageResponse(result=subscription_id, msg_id=req.id)
        self.write_message(res.to_json())

        observable = self._exposed_thing.observe(
            name=params["name"],
            request_type=params["request_type"])

        subscription = observable.observe_on(self._scheduler).subscribe(
            on_next=_on_next,
            on_error=_on_error,
            on_completed=_on_completed)

        self._subscriptions[subscription_id] = subscription

    @gen.coroutine
    def _handle_dispose(self, req):
        """"""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_DISPOSE)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        result = None
        subscription_id = params["subscription"]

        if subscription_id in self._subscriptions:
            self._dispose_subscription(subscription_id)
            result = subscription_id

        res = WebsocketMessageResponse(result=result, msg_id=req.id)
        self.write_message(res.to_json())

    @gen.coroutine
    def _handle(self, req):
        """"""

        handler_map = {
            WebsocketMethods.GET_PROPERTY: self._handle_get_property,
            WebsocketMethods.SET_PROPERTY: self._handle_set_property,
            WebsocketMethods.OBSERVE: self._handle_observe,
            WebsocketMethods.DISPOSE: self._handle_dispose
        }

        if req.method not in handler_map:
            self._write_error("Unimplemented method", WebsocketErrors.INTERNAL_ERROR, msg_id=req.id)
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
            self._write_error(str(ex), WebsocketErrors.INTERNAL_ERROR)

    def on_close(self):
        """"""

        pass
