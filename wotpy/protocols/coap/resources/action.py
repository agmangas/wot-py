#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP resources to deal with Action interactions.
"""

import datetime
import json
import logging
import uuid

import aiocoap
import aiocoap.error
import aiocoap.resource
import tornado.concurrent
import tornado.gen
import tornado.ioloop

from wotpy.protocols.coap.resources.utils import parse_request_opt_query

JSON_CONTENT_FORMAT = 50


def get_thing_action(server, request):
    """Takes a CoAP request and returns the Thing Action
    identified by the request arguments."""

    query = parse_request_opt_query(request)
    url_name_thing = query.get("thing")
    url_name_action = query.get("name")

    if not url_name_thing or not url_name_action:
        raise aiocoap.error.BadRequest("Missing query arguments")

    exposed_thing = server.exposed_thing_set.find_by_thing_id(url_name_thing)

    if not exposed_thing:
        raise aiocoap.error.NotFound("Thing not found")

    try:
        return next(
            exposed_thing.actions[key] for key in exposed_thing.actions
            if exposed_thing.actions[key].url_name == url_name_action)
    except StopIteration:
        raise aiocoap.error.NotFound("Action not found")


class ActionResource(aiocoap.resource.ObservableResource):
    """CoAP resource to invoke Actions and observe those invocations."""

    DEFAULT_CLEAR_MS = 1000 * 60 * 5

    def __init__(self, server, clear_ms=None):
        super(ActionResource, self).__init__()
        self._server = server
        self._clear_ms = self.DEFAULT_CLEAR_MS if clear_ms is None else clear_ms
        self._pending_actions = {}
        self._logr = logging.getLogger(__name__)

    @tornado.gen.coroutine
    def render_get(self, request):
        """Handler to check the status of an ongoing invocation."""

        request_payload = json.loads(request.payload)
        invocation_id = request_payload.get("id", None)

        self._logr.debug("Action GET request for invocation: {}".format(invocation_id))

        if invocation_id is None:
            raise aiocoap.error.BadRequest("Missing invocation ID")

        if invocation_id not in self._pending_actions:
            raise aiocoap.error.NotFound("Unknown invocation")

        future_result = self._pending_actions[invocation_id]

        def raise_response(the_resp_dict):
            response_payload = json.dumps(the_resp_dict).encode("utf-8")
            response = aiocoap.Message(code=aiocoap.Code.CONTENT, payload=response_payload)
            response.opt.content_format = JSON_CONTENT_FORMAT
            raise tornado.gen.Return(response)

        if not future_result.done():
            self._logr.debug("Invocation ({}) is still pending".format(invocation_id))
            raise_response({"id": invocation_id, "done": False})

        resp_dict = {"done": True, "id": invocation_id}

        try:
            result = future_result.result()
            resp_dict.update({"result": result})
        except Exception as ex:
            resp_dict.update({"error": str(ex)})

        self._logr.debug("Returning invocation: {}".format(invocation_id))

        raise_response(resp_dict)

    @tornado.gen.coroutine
    def add_observation(self, request, server_observation):
        """Method that decides whether to add a new observer.
        Observers are added for GET requests (checks for invocation status)
        but not for POST requests (action invocations)."""

        if request.code.name != aiocoap.Code.GET.name:
            return

        try:
            request_payload = json.loads(request.payload)
        except (TypeError, json.decoder.JSONDecodeError):
            return

        invocation_id = request_payload.get("id", None)

        if invocation_id not in self._pending_actions:
            self._logr.debug("Observation rejected (unknown invocation): {}".format(invocation_id))
            return

        def cancellation_cb():
            self._logr.debug("Observation cancel callback for invocation: {}".format(invocation_id))

        self._logr.debug("Added observation for invocation: {}".format(invocation_id))

        server_observation.accept(cancellation_cb)

        # noinspection PyUnusedLocal
        def trigger_cb(ft):
            self._logr.debug("Triggering observation for invocation: {}".format(invocation_id))
            server_observation.trigger()

        future_result = self._pending_actions[invocation_id]
        tornado.concurrent.future_add_done_callback(future_result, trigger_cb)

    @tornado.gen.coroutine
    def render_post(self, request):
        """Handler for action invocations."""

        thing_action = get_thing_action(self._server, request)

        self._logr.debug("Action POST request: {}".format(thing_action))

        request_payload = json.loads(request.payload)

        if "input" not in request_payload:
            raise aiocoap.error.BadRequest("Missing input value")

        invocation_id = uuid.uuid4().hex

        def clear_cb():
            self._logr.debug("Removing pending invocation: {}".format(invocation_id))
            self._pending_actions.pop(invocation_id, None)

        # noinspection PyUnusedLocal
        def done_cb(fut):
            loop = tornado.ioloop.IOLoop.current()
            self._logr.debug("Invocation done ({}): cleaning on {} ms".format(invocation_id, self._clear_ms))
            loop.add_timeout(datetime.timedelta(milliseconds=self._clear_ms), clear_cb)

        input_value = request_payload.get("input")
        fut_action = tornado.gen.convert_yielded(thing_action.invoke(input_value))
        tornado.concurrent.future_add_done_callback(fut_action, done_cb)
        self._pending_actions[invocation_id] = fut_action
        response_payload = json.dumps({"id": invocation_id}).encode("utf-8")
        response = aiocoap.Message(code=aiocoap.Code.CREATED, payload=response_payload)
        response.opt.content_format = JSON_CONTENT_FORMAT

        raise tornado.gen.Return(response)
