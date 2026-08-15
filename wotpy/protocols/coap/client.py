#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Classes that contain the client logic for the CoAP protocol.
"""

import asyncio
import json
import logging
import time
from urllib.parse import urlparse

import aiocoap
import reactivex

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.coap.enums import CoAPSchemes
from wotpy.protocols.coap.credential import BaseCredential
from wotpy.protocols.enums import Protocols, InteractionVerbs
from wotpy.protocols.exceptions import FormNotFoundException, ProtocolClientException, ClientRequestTimeout
from wotpy.protocols.utils import is_scheme_form
from wotpy.utils.utils import handle_observer_finalization
from wotpy.wot.events import PropertyChangeEventInit, PropertyChangeEmittedEvent, EmittedEvent


class CoAPClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the CoAP protocol."""

    def __init__(self, credentials=None):
        self._logr = logging.getLogger(__name__)
        self._credentials = credentials
        self._coap_client = None
        self._client_lock = asyncio.Lock()
        self._credential = None
        super().__init__()

    @classmethod
    def _pick_coap_href(cls, td, forms, op=None):
        """Picks the most appropriate CoAP form href from the given list of forms."""

        def is_op_form(form):
            try:
                return op is None or op == form.op or op in form.op
            except TypeError:
                return False

        def find_href(scheme):
            try:
                return next(
                    form.href for form in forms
                    if is_scheme_form(form, td.base, scheme) and is_op_form(form))
            except StopIteration:
                return None

        form_coaps = find_href(CoAPSchemes.COAPS)

        return form_coaps if form_coaps is not None else find_href(CoAPSchemes.COAP)

    @classmethod
    def _assert_success(cls, res):
        """Asserts that the given CoAP response was successful and raises an Exception if not."""

        if not res.code.is_successful():
            raise ProtocolClientException("Unsuccessful CoAP response: {}".format(res.payload.decode("utf-8")))

    def _build_subscribe(self, href, next_item_builder):
        """Builds the subscribe function that should be passed when
        constructing an Observable linked to an observable CoAP resurce."""

        def subscribe(observer, scheduler):
            """Subscription function to observe resources using the CoAP protocol."""

            query = urlparse(href).query

            state = {
                "active": True,
                "request": None,
                "pending": None
            }

            @handle_observer_finalization(observer)
            async def callback():
                self._logr.debug("Creating CoAP client for observation: {}".format(query))

                coap_client = await aiocoap.Context.create_client_context()
                if self._credentials:
                    with open(self._credentials, "rb") as file:
                        coap_client.client_credentials.load_from_dict(json.load(file))

                try:
                    msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href, observe=0)
                    state["request"] = coap_client.request(await self.sign_request(msg))

                    self._logr.debug("Sending observation request: {}".format(msg))

                    future_first_resp = state["request"].response
                    state["pending"] = future_first_resp
                    first_resp = await future_first_resp
                    state["pending"] = None
                    self._assert_success(first_resp)
                    next_item = next_item_builder(first_resp.payload)
                    next_item is not None and observer.on_next(next_item)

                    while state["active"]:
                        next_obsv_gen = state["request"].observation.__aiter__().__anext__()
                        future_resp = asyncio.ensure_future(next_obsv_gen)
                        state["pending"] = future_resp
                        resp = await future_resp
                        state["pending"] = None
                        self._assert_success(resp)
                        next_item = next_item_builder(resp.payload)
                        next_item is not None and observer.on_next(next_item)

                    self._logr.debug("Terminated subscription callback for: {}".format(query))
                finally:
                    await coap_client.shutdown()

            def unsubscribe():
                self._logr.debug("Unsubscribing from: {}".format(query))

                state["active"] = False

                if state["request"] and not state["request"].observation.cancelled:
                    self._logr.debug("Cancelling observation on: {}".format(query))
                    state["request"].observation.cancel()

                if state["pending"]:
                    self._logr.debug("Cancelling pending request: {}".format(state["pending"]))
                    state["pending"].cancel()

            asyncio.create_task(callback())

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

    def set_security(self, security_scheme_dict, credentials):
        """Sets the security credentials for the given security scheme."""

        credential = BaseCredential.build(security_scheme_dict, credentials)
        self._credential = credential

    async def sign_request(self, request):
        """Adds the appropriate authorization header to the request
        and delegates the addition of the header to the credential class."""

        if self._credential:
            return await self._credential.sign(request)

        return request

    async def _invocation_create(self, coap_client, href, input_value, timeout=None):
        """Creates a new action invocation by sending a POST request."""

        payload = json.dumps({"input": input_value}).encode("utf-8")
        msg = aiocoap.Message(code=aiocoap.Code.POST, payload=payload, uri=href)
        request = coap_client.request(await self.sign_request(msg))

        try:
            response = await asyncio.wait_for(request.response, timeout=timeout)
        except asyncio.TimeoutError:
            raise ClientRequestTimeout

        self._assert_success(response)

        invocation_id = json.loads(response.payload).get("id")

        return invocation_id

    async def _invocation_observe(self, coap_client, href, invocation_id, timeout=None):
        """Starts observing an existing action invocation by sending a GET request."""

        payload = json.dumps({"id": invocation_id}).encode("utf-8")
        msg = aiocoap.Message(code=aiocoap.Code.GET, payload=payload, uri=href, observe=0)
        request = coap_client.request(await self.sign_request(msg))

        try:
            response = await asyncio.wait_for(request.response, timeout=timeout)
        except asyncio.TimeoutError:
            raise ClientRequestTimeout

        self._assert_success(response)

        return request, response

    async def _invocation_next(self, request, timeout=None):
        """Waits for the next item in an active action invocation observation."""

        try:
            response = await asyncio.wait_for(
                request.observation.__aiter__().__anext__(),
                timeout=timeout)
        except asyncio.TimeoutError:
            raise ClientRequestTimeout

        self._assert_success(response)

        return response

    async def invoke_action(self, td, name, input_value, timeout=None):
        """Invokes an Action on a remote Thing."""

        href = self._pick_coap_href(
            td, td.get_action_forms(name),
            op=InteractionVerbs.INVOKE_ACTION)

        if href is None:
            raise FormNotFoundException()

        coap_client = await aiocoap.Context.create_client_context()
        if self._credentials:
            with open(self._credentials, "rb") as file:
                coap_client.client_credentials.load_from_dict(json.load(file))

        try:
            invocation_id = await self._invocation_create(
                coap_client, href, input_value, timeout=timeout)

            request_obsv, response_obsv = await self._invocation_observe(
                coap_client, href, invocation_id, timeout=timeout)

            invocation_status = json.loads(response_obsv.payload)

            now = time.time()

            while not invocation_status.get("done"):
                if timeout and (time.time() - now) > timeout:
                    raise ClientRequestTimeout

                response_obsv = await self._invocation_next(request_obsv, timeout=timeout)
                invocation_status = json.loads(response_obsv.payload)

            if not request_obsv.observation.cancelled:
                request_obsv.observation.cancel()

            if invocation_status.get("error"):
                raise Exception(invocation_status.get("error"))
            else:
                return invocation_status.get("result")
        finally:
            await coap_client.shutdown()

    async def write_property(self, td, name, value, timeout=None):
        """Updates the value of a Property on a remote Thing."""

        href = self._pick_coap_href(
            td, td.get_property_forms(name),
            op=InteractionVerbs.WRITE_PROPERTY)

        if href is None:
            raise FormNotFoundException()

        coap_client = await aiocoap.Context.create_client_context()
        if self._credentials:
            with open(self._credentials, "rb") as file:
                coap_client.client_credentials.load_from_dict(json.load(file))

        try:
            payload = json.dumps({"value": value}).encode("utf-8")
            msg = aiocoap.Message(code=aiocoap.Code.PUT, payload=payload, uri=href)
            request = coap_client.request(await self.sign_request(msg))

            try:
                response = await asyncio.wait_for(request.response, timeout=timeout)
            except asyncio.TimeoutError:
                raise ClientRequestTimeout

            self._assert_success(response)
        finally:
            await coap_client.shutdown()

    async def read_property(self, td, name, timeout=None):
        """Reads the value of a Property on a remote Thing."""

        href = self._pick_coap_href(
            td, td.get_property_forms(name),
            op=InteractionVerbs.READ_PROPERTY)

        if href is None:
            raise FormNotFoundException()

        coap_client = await aiocoap.Context.create_client_context()
        if self._credentials:
            with open(self._credentials, "rb") as file:
                coap_client.client_credentials.load_from_dict(json.load(file))

        try:
            msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href)
            request = coap_client.request(await self.sign_request(msg))

            try:
                response = await asyncio.wait_for(request.response, timeout=timeout)
            except asyncio.TimeoutError:
                raise ClientRequestTimeout

            self._assert_success(response)

            prop_value = json.loads(response.payload).get("value")

            return prop_value
        finally:
            await coap_client.shutdown()

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        href = self._pick_coap_href(
            td, td.get_property_forms(name),
            op=InteractionVerbs.OBSERVE_PROPERTY)

        if href is None:
            raise FormNotFoundException()

        def next_item_builder(payload):
            value = json.loads(payload).get("value")
            init = PropertyChangeEventInit(name=name, value=value)
            return PropertyChangeEmittedEvent(init=init)

        subscribe = self._build_subscribe(href, next_item_builder)

        return reactivex.create(subscribe)

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        href = self._pick_coap_href(
            td, td.get_event_forms(name),
            op=InteractionVerbs.SUBSCRIBE_EVENT)

        if href is None:
            raise FormNotFoundException()

        def next_item_builder(payload):
            if payload:
                data = json.loads(payload).get("data")
                return EmittedEvent(init=data, name=name)
            else:
                return None

        subscribe = self._build_subscribe(href, next_item_builder)

        return reactivex.create(subscribe)

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
