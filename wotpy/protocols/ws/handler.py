#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that handles incoming WebSockets messages.
"""

import uuid

from jsonschema import validate, ValidationError
from rx.concurrency import IOLoopScheduler
from tornado import websocket, gen

from wotpy.protocols.ws.enums import WebsocketMethods, WebsocketErrors
from wotpy.protocols.ws.messages import \
    WebsocketMessageRequest, \
    WebsocketMessageException, \
    WebsocketMessageError, \
    WebsocketMessageResponse, \
    WebsocketMessageEmittedItem
from wotpy.protocols.ws.schemas import \
    SCHEMA_PARAMS_READ_PROPERTY, \
    SCHEMA_PARAMS_WRITE_PROPERTY, \
    SCHEMA_PARAMS_DISPOSE, \
    SCHEMA_PARAMS_INVOKE_ACTION, \
    SCHEMA_PARAMS_ON_PROPERTY_CHANGE, \
    SCHEMA_PARAMS_ON_TD_CHANGE, \
    SCHEMA_PARAMS_ON_EVENT


# noinspection PyAbstractClass
class WebsocketHandler(websocket.WebSocketHandler):
    """Tornado handler for Websocket messages.
    This class processes all incoming WebSocket messages and
    translates them to actions executed on ExposedThing objects."""

    POLICY_VIOLATION_CODE = 1008
    POLICY_VIOLATION_REASON = "Not found"

    def __init__(self, *args, **kwargs):
        self._server = kwargs.pop("websocket_server", None)
        self._scheduler = IOLoopScheduler()
        self._subscriptions = {}
        self._exposed_thing_name = None
        super(WebsocketHandler, self).__init__(*args, **kwargs)

    @property
    def exposed_thing(self):
        """Exposed thing property.
        Retrieves the ExposedThing from the parent server."""

        try:
            return self._server.get_exposed_thing(self._exposed_thing_name)
        except ValueError:
            self.close(self.POLICY_VIOLATION_CODE, self.POLICY_VIOLATION_REASON)

    def check_origin(self, origin):
        """Should return True to accept the request or False to reject it.
        The origin argument is the value of the Origin HTTP header,
        the url responsible for initiating this request"""

        # ToDo: Check this once we add authentication
        # This is extremely dangerous in case of a cookie-based authentication system.
        # WS authentication should be handled independently with some kind of token-based system.

        return True

    def open(self, name):
        """Called when the WebSockets connection is opened."""

        assert self._exposed_thing_name is None

        try:
            self._server.get_exposed_thing(name)
            self._exposed_thing_name = name
        except ValueError:
            self.close(self.POLICY_VIOLATION_CODE, self.POLICY_VIOLATION_REASON)

    def _write_error(self, message, code, msg_id=None, data=None):
        """Builds an error message instance and sends it to the client."""

        err = WebsocketMessageError(message=message, code=code, data=data, msg_id=msg_id)
        self.write_message(err.to_json())

    def _dispose_subscription(self, subscription_id):
        """Takes a subscription ID and destroys the related subscription."""

        if subscription_id in self._subscriptions:
            subscription = self._subscriptions.pop(subscription_id)
            subscription.dispose()

    def _on_subscription_error(self, subscription_id, err):
        """Default error callback for Observable subscriptions."""

        self._dispose_subscription(subscription_id)
        data_err = {"subscription": subscription_id}
        self._write_error(str(err), WebsocketErrors.SUBSCRIPTION_ERROR, data=data_err)

    def _on_subscription_next(self, subscription_id, item):
        """Default next callback for Observable subscriptions."""

        try:
            msg = WebsocketMessageEmittedItem(
                subscription_id=subscription_id,
                name=item.name,
                data=item.data)
            self.write_message(msg.to_json())
        except WebsocketMessageException as ex:
            self._on_subscription_error(subscription_id, ex)

    def _on_subscription_completed(self, subscription_id):
        """Default completed callback for Observable subscriptions."""

        self._dispose_subscription(subscription_id)

    def _subscribe(self, subscription_id, observable):
        """Subscribe to the given Observable and add the subscription handler to the internal dict."""

        subscription = observable.observe_on(self._scheduler).subscribe(
            on_next=lambda item: self._on_subscription_next(subscription_id, item),
            on_error=lambda err: self._on_subscription_error(subscription_id, err),
            on_completed=lambda: self._on_subscription_completed(subscription_id))

        self._subscriptions[subscription_id] = subscription

    @gen.coroutine
    def _handle_get_property(self, req):
        """Handler for the 'get_property' method."""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_READ_PROPERTY)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        try:
            prop_value = yield self.exposed_thing.read_property(name=params["name"])
        except Exception as ex:
            self._write_error(str(ex), WebsocketErrors.INTERNAL_ERROR, msg_id=req.id)
            return

        res = WebsocketMessageResponse(result=prop_value, msg_id=req.id)
        self.write_message(res.to_json())

    @gen.coroutine
    def _handle_set_property(self, req):
        """Handler for the 'set_property' method."""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_WRITE_PROPERTY)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        try:
            yield self.exposed_thing.write_property(name=params["name"], value=params["value"])
        except Exception as ex:
            self._write_error(str(ex), WebsocketErrors.INTERNAL_ERROR, msg_id=req.id)
            return

        res = WebsocketMessageResponse(result=None, msg_id=req.id)
        self.write_message(res.to_json())

    @gen.coroutine
    def _handle_invoke_action(self, req):
        """Handler for the 'invoke_action' method."""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_INVOKE_ACTION)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        try:
            input_value = params.get("parameters")
            action_result = yield self.exposed_thing.invoke_action(params["name"], input_value)
        except Exception as ex:
            self._write_error(str(ex), WebsocketErrors.INTERNAL_ERROR, msg_id=req.id)
            return

        res = WebsocketMessageResponse(result=action_result, msg_id=req.id)
        self.write_message(res.to_json())

    @gen.coroutine
    def _handle_on_property_change(self, req):
        """Handler for the 'on_property_change' subscription method."""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_ON_PROPERTY_CHANGE)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        subscription_id = str(uuid.uuid4())

        res = WebsocketMessageResponse(result=subscription_id, msg_id=req.id)
        self.write_message(res.to_json())

        observable = self.exposed_thing.on_property_change(name=params["name"])

        self._subscribe(subscription_id, observable)

    @gen.coroutine
    def _handle_on_td_change(self, req):
        """Handler for the 'on_td_change' subscription method."""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_ON_TD_CHANGE)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        subscription_id = str(uuid.uuid4())

        res = WebsocketMessageResponse(result=subscription_id, msg_id=req.id)
        self.write_message(res.to_json())

        observable = self.exposed_thing.on_td_change()

        self._subscribe(subscription_id, observable)

    @gen.coroutine
    def _handle_on_event(self, req):
        """Handler for the 'on_event' subscription method."""

        params = req.params

        try:
            validate(params, SCHEMA_PARAMS_ON_EVENT)
        except ValidationError as ex:
            self._write_error(str(ex), WebsocketErrors.INVALID_METHOD_PARAMS, msg_id=req.id)
            return

        subscription_id = str(uuid.uuid4())

        res = WebsocketMessageResponse(result=subscription_id, msg_id=req.id)
        self.write_message(res.to_json())

        observable = self.exposed_thing.on_event(name=params["name"])

        self._subscribe(subscription_id, observable)

    @gen.coroutine
    def _handle_dispose(self, req):
        """Handler for the 'dispose' method."""

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
        """Takes a WebsocketMessageRequest instance and routes
        the request to the required method handler."""

        handler_map = {
            WebsocketMethods.READ_PROPERTY: self._handle_get_property,
            WebsocketMethods.WRITE_PROPERTY: self._handle_set_property,
            WebsocketMethods.INVOKE_ACTION: self._handle_invoke_action,
            WebsocketMethods.ON_PROPERTY_CHANGE: self._handle_on_property_change,
            WebsocketMethods.ON_TD_CHANGE: self._handle_on_td_change,
            WebsocketMethods.ON_EVENT: self._handle_on_event,
            WebsocketMethods.DISPOSE: self._handle_dispose,
        }

        if req.method not in handler_map:
            self._write_error("Unimplemented method", WebsocketErrors.INTERNAL_ERROR, msg_id=req.id)
            return

        handler = handler_map[req.method]
        yield handler(req)

    @gen.coroutine
    def on_message(self, message):
        """Called each time the server receives a WebSockets message.
        All messages that do not conform to the protocol are discarded."""

        try:
            req = WebsocketMessageRequest.from_raw(message)
            gen.convert_yielded(self._handle(req))
        except WebsocketMessageException as ex:
            self._write_error(str(ex), WebsocketErrors.INTERNAL_ERROR)

    def on_close(self):
        """Called when the WebSockets connection is closed."""

        for subscription_id in list(self._subscriptions.keys()):
            self._dispose_subscription(subscription_id)
