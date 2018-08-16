#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the HTTP protocol.
"""

import json

import tornado.concurrent
import tornado.gen
import tornado.httpclient
from rx import Observable

from wotpy.protocols.client import BaseProtocolClient, ProtocolClientException
from wotpy.protocols.enums import Protocols
from wotpy.protocols.http.enums import HTTPSchemes
from wotpy.protocols.utils import is_scheme_form
from wotpy.wot.events import EmittedEvent


class HTTPClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the Websocket protocol."""

    REL_OBSERVE = "observeProperty"

    @property
    def protocol(self):
        """Protocol of this client instance.
        A member of the Protocols enum."""

        return Protocols.HTTP

    def is_supported_interaction(self, td, name):
        """"""

        raise NotImplementedError

    @tornado.gen.coroutine
    def invoke_action(self, td, name, input_value):
        """"""

        raise NotImplementedError

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        """"""

        raise NotImplementedError

    @tornado.gen.coroutine
    def read_property(self, td, name):
        """"""

        raise NotImplementedError

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        try:
            href = next(
                form.href for form in td.get_event_forms(name)
                if is_scheme_form(form, td.base, HTTPSchemes.list()) and form.rel == self.REL_OBSERVE)
        except StopIteration:
            raise ProtocolClientException("Undefined event form")

        def subscribe(observer):
            """Subscription function to observe events using the HTTP protocol."""

            state = {"active": True}

            def on_response(ft):
                try:
                    response = ft.result()
                    payload = json.loads(response.body).get("payload")
                    observer.on_next(EmittedEvent(init=payload, name=name))
                    if state["active"]:
                        fetch_response()
                except Exception as ex:
                    observer.on_error(ex)

            def fetch_response():
                http_client = tornado.httpclient.AsyncHTTPClient()
                http_request = tornado.httpclient.HTTPRequest(href, method="GET")
                future_response = http_client.fetch(http_request)
                tornado.concurrent.future_add_done_callback(future_response, on_response)

            def unsubscribe():
                state["active"] = False

            fetch_response()

            return unsubscribe

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        raise NotImplementedError

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
