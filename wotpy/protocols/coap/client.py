#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the CoAP protocol.
"""

import json

import aiocoap
import tornado.gen

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.coap.enums import CoAPSchemes
from wotpy.protocols.enums import Protocols
from wotpy.protocols.exceptions import FormNotFoundException, ProtocolClientException
from wotpy.protocols.utils import is_scheme_form


class CoAPClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the CoAP protocol."""

    @classmethod
    def pick_coap_href(cls, td, forms, rel=None):
        """Picks the most appropriate CoAP form href from the given list of forms."""

        def find_href(scheme):
            try:
                return next(
                    form.href for form in forms
                    if is_scheme_form(form, td.base, scheme) and (rel is None or form.rel == rel))
            except StopIteration:
                return None

        form_coaps = find_href(CoAPSchemes.COAPS)

        return form_coaps if form_coaps is not None else find_href(CoAPSchemes.COAP)

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

        raise NotImplementedError

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        href = self.pick_coap_href(td, td.get_property_forms(name))

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

        href = self.pick_coap_href(td, td.get_property_forms(name))

        if href is None:
            raise FormNotFoundException()

        coap_client = yield aiocoap.Context.create_client_context()
        msg = aiocoap.Message(code=aiocoap.Code.GET, uri=href)
        response = yield coap_client.request(msg).response
        prop_value = json.loads(response.payload).get("value")

        raise tornado.gen.Return(prop_value)

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        raise NotImplementedError

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
