#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP resources to deal with Action interactions.
"""

import json
import uuid

import aiocoap
import aiocoap.error
import aiocoap.resource
import tornado.concurrent
import tornado.gen
import tornado.ioloop

JSON_CONTENT_FORMAT = 50


class ActionInvokeResource(aiocoap.resource.ObservableResource):
    """CoAP resource to observe property updates."""

    def __init__(self, exposed_thing, name):
        super(ActionInvokeResource, self).__init__()
        self._exposed_thing = exposed_thing
        self._name = name
        self._pending_actions = {}

    @tornado.gen.coroutine
    def add_observation(self, request, server_observation):
        """"""

        if request.code.name != aiocoap.Code.GET.name:
            return

        try:
            request_payload = json.loads(request.payload)
        except (TypeError, json.decoder.JSONDecodeError):
            return

        invocation_id = request_payload.get("invocation", None)

        if invocation_id not in self._pending_actions:
            return

        def cancellation_cb():
            pass

        server_observation.accept(cancellation_cb)

        # noinspection PyUnusedLocal
        def trigger_cb(ft):
            server_observation.trigger()

        future_result = self._pending_actions[invocation_id]
        tornado.concurrent.future_add_done_callback(future_result, trigger_cb)

    @tornado.gen.coroutine
    def render_get(self, request):
        """"""

        request_payload = json.loads(request.payload)
        invocation_id = request_payload.get("invocation", None)

        if invocation_id is None:
            raise aiocoap.error.BadRequest(b"Missing invocation ID")

        if invocation_id not in self._pending_actions:
            raise aiocoap.error.NotFound(b"Unknown invocation")

        future_result = self._pending_actions[invocation_id]

        def raise_response(the_resp_dict):
            response_payload = json.dumps(the_resp_dict).encode("utf-8")
            response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=response_payload)
            response.opt.content_format = JSON_CONTENT_FORMAT
            raise tornado.gen.Return(response)

        if not future_result.done():
            raise_response({"done": False})

        resp_dict = {}

        try:
            result = future_result.result()
            resp_dict.update({"done": True, "result": result})
        except Exception as ex:
            resp_dict.update({"done": True, "error": str(ex)})

        raise_response(resp_dict)

    @tornado.gen.coroutine
    def render_post(self, request):
        """"""

        request_payload = json.loads(request.payload)

        if "input" not in request_payload:
            raise aiocoap.error.BadRequest(b"Missing input value")

        input_value = request_payload.get("input")
        future_action = self._exposed_thing.actions[self._name].invoke(input_value)
        invocation_id = uuid.uuid4().hex
        self._pending_actions[invocation_id] = future_action
        response_payload = json.dumps({"invocation": invocation_id}).encode("utf-8")
        response = aiocoap.Message(code=aiocoap.Code.CREATED, payload=response_payload)
        response.opt.content_format = JSON_CONTENT_FORMAT

        raise tornado.gen.Return(response)
