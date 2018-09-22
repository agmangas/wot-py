#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the CoAP protocol.
"""

import json

import aiocoap
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.platform.asyncio
from rx import Observable

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.coap.enums import CoAPSchemes
from wotpy.protocols.enums import Protocols, InteractionVerbs
from wotpy.protocols.exceptions import FormNotFoundException, ProtocolClientException
from wotpy.protocols.utils import is_scheme_form
from wotpy.wot.events import PropertyChangeEventInit, PropertyChangeEmittedEvent, EmittedEvent


class CoAPClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the CoAP protocol."""

    @classmethod
    def _pick_coap_href(cls, td, forms, rel=None):
        """Picks the most appropriate CoAP form href from the given list of forms."""

        def is_rel_form(form):
            try:
                return rel is None or rel == form.rel or rel in form.rel
            except TypeError:
                return False

        def find_href(scheme):
            try:
                return next(
                    form.href for form in forms
                    if is_scheme_form(form, td.base, scheme) and is_rel_form(form))
            except StopIteration:
                return None

        form_coaps = find_href(CoAPSchemes.COAPS)

        return form_coaps if form_coaps is not None else find_href(CoAPSchemes.COAP)

    @classmethod
    def _build_subscribe(cls, href, next_item_builder):
        """Builds the subscribe function that should be passed when
        constructing an Observable linked to an observable CoAP resurce."""

        def subscribe(observer):
            """Subscription function to observe resources using the CoAP protocol."""

            state = {
                "active": True,
                "request": None,
                "pending_future": None
            }

            def on_response(ft):
                try:
                    state["pending_future"] = None

                    response = ft.result()
                    next_item = next_item_builder(response.payload)

                    if next_item is not None:
                        observer.on_next(next_item)

                    if state["active"]:
                        next_observation_gen = state["request"].observation.__aiter__().__anext__()
                        future_response = tornado.gen.convert_yielded(next_observation_gen)
                        state["pending_future"] = future_response
                        tornado.ioloop.IOLoop.current().add_future(future_response, on_response)
                except Exception as exc:
                    observer.on_error(exc)

            def on_coap_client(ft):
                try:
                    coap_client = ft.result()
                    msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href, observe=0)
                    state["request"] = coap_client.request(msg)
                    future_first_response = state["request"].response
                    state["pending_future"] = future_first_response
                    tornado.ioloop.IOLoop.current().add_future(future_first_response, on_response)
                except Exception as exc:
                    observer.on_error(exc)

            def unsubscribe():
                if state["request"]:
                    state["request"].observation.cancel()

                if state["pending_future"]:
                    state["pending_future"].cancel()

                state["active"] = False

            try:
                coap_client_gen = aiocoap.Context.create_client_context()
                future_coap_client = tornado.gen.convert_yielded(coap_client_gen)
                tornado.concurrent.future_add_done_callback(future_coap_client, on_coap_client)
            except Exception as ex:
                observer.on_error(ex)

            return unsubscribe

        return subscribe

    @property
    def protocol(self):
        """Protocol of this client instance.
        A member of the Protocols enum."""

        return Protocols.COAP

    def is_supported_interaction(self, td, name):
        """Returns True if the any of the Forms for the Interaction
        with the given name is supported in this Protocol Binding client."""

        forms = td.get_forms(name)

        forms_coap = [
            form for form in forms
            if is_scheme_form(form, td.base, CoAPSchemes.list())
        ]

        return len(forms_coap) > 0

    @tornado.gen.coroutine
    def invoke_action(self, td, name, input_value):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        href = self._pick_coap_href(td, td.get_action_forms(name))

        if href is None:
            raise FormNotFoundException()

        coap_client = yield aiocoap.Context.create_client_context()

        payload = json.dumps({"input": input_value}).encode("utf-8")
        msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
        response = yield coap_client.request(msg).response
        invocation_id = json.loads(response.payload).get("invocation")

        payload_obsv = json.dumps({"invocation": invocation_id}).encode("utf-8")
        msg_obsv = aiocoap.Message(code=aiocoap.Code.GET, payload=payload_obsv, uri=href, observe=0)
        request_obsv = coap_client.request(msg_obsv)
        first_response_obsv = yield request_obsv.response

        invocation_status = json.loads(first_response_obsv.payload)

        while not invocation_status.get("done"):
            response_obsv = yield request_obsv.observation.__aiter__().__anext__()
            invocation_status = json.loads(response_obsv.payload)

        if invocation_status.get("error"):
            raise Exception(invocation_status.get("error"))
        else:
            raise tornado.gen.Return(invocation_status.get("result"))

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        href = self._pick_coap_href(td, td.get_property_forms(name))

        if href is None:
            raise FormNotFoundException()

        coap_client = yield aiocoap.Context.create_client_context()
        payload = json.dumps({"value": value}).encode("utf-8")
        msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
        response = yield coap_client.request(msg).response

        if not response.code.is_successful():
            raise ProtocolClientException(str(response.code))

    @tornado.gen.coroutine
    def read_property(self, td, name):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        href = self._pick_coap_href(td, td.get_property_forms(name))

        if href is None:
            raise FormNotFoundException()

        coap_client = yield aiocoap.Context.create_client_context()
        msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href)
        response = yield coap_client.request(msg).response
        prop_value = json.loads(response.payload).get("value")

        raise tornado.gen.Return(prop_value)

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        href = self._pick_coap_href(td, td.get_property_forms(name), rel=InteractionVerbs.OBSERVE_PROPERTY)

        if href is None:
            raise FormNotFoundException()

        def next_item_builder(payload):
            value = json.loads(payload).get("value")
            init = PropertyChangeEventInit(name=name, value=value)
            return PropertyChangeEmittedEvent(init=init)

        subscribe = self._build_subscribe(href, next_item_builder)

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        href = self._pick_coap_href(td, td.get_event_forms(name))

        if href is None:
            raise FormNotFoundException()

        def next_item_builder(payload):
            if payload:
                data = json.loads(payload).get("data")
                return EmittedEvent(init=data, name=name)
            else:
                return None

        subscribe = self._build_subscribe(href, next_item_builder)

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
