#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the HTTP protocol.
"""

import json

import tornado.concurrent
import tornado.gen
import tornado.httpclient
import tornado.ioloop
from rx import Observable
from six.moves.urllib import parse

from wotpy.protocols.client import BaseProtocolClient, ProtocolClientException
from wotpy.protocols.enums import Protocols, InteractionVerbs
from wotpy.protocols.http.enums import HTTPSchemes
from wotpy.protocols.utils import is_scheme_form
from wotpy.wot.events import EmittedEvent, PropertyChangeEmittedEvent, PropertyChangeEventInit


class HTTPClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the Websocket protocol."""

    JSON_HEADERS = {"Content-Type": "application/json"}

    @classmethod
    def pick_http_href(cls, td, forms, rel=None):
        """Picks the most appropriate HTTP form href from the given list of forms."""

        def find_href(scheme):
            try:
                return next(
                    form.href for form in forms
                    if is_scheme_form(form, td.base, scheme) and (rel is None or form.rel == rel))
            except StopIteration:
                return None

        form_https = find_href(HTTPSchemes.HTTPS)

        return form_https if form_https is not None else find_href(HTTPSchemes.HTTP)

    @property
    def protocol(self):
        """Protocol of this client instance.
        A member of the Protocols enum."""

        return Protocols.HTTP

    def is_supported_interaction(self, td, name):
        """Returns True if the any of the Forms for the Interaction
        with the given name is supported in this Protocol Binding client."""

        forms = td.get_forms(name)

        forms_http = [
            form for form in forms
            if is_scheme_form(form, td.base, HTTPSchemes.list())
        ]

        return len(forms_http) > 0

    @tornado.gen.coroutine
    def invoke_action(self, td, name, input_value, check_interval_ms=800):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        href = self.pick_http_href(td, td.get_action_forms(name))

        if href is None:
            raise ProtocolClientException("Unable to find the action form")

        body = json.dumps({"input": input_value})
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="POST", body=body, headers=self.JSON_HEADERS)
        response = yield http_client.fetch(http_request)
        invocation_url = json.loads(response.body).get("invocation")

        future_result = tornado.concurrent.Future()

        @tornado.gen.coroutine
        def check_invocation():
            parsed = parse.urlparse(href)
            href_invoc = "{}://{}/{}".format(parsed.scheme, parsed.netloc, invocation_url.lstrip("/"))
            http_request_invoc = tornado.httpclient.HTTPRequest(href_invoc, method="GET")
            response_invoc = yield http_client.fetch(http_request_invoc)
            status = json.loads(response_invoc.body)

            if status.get("done") is False:
                return

            if status.get("error") is not None:
                future_result.set_exception(Exception(status.get("error")))
            else:
                future_result.set_result(status.get("result"))

        periodic_check = tornado.ioloop.PeriodicCallback(check_invocation, check_interval_ms)

        try:
            periodic_check.start()
            result = yield future_result
            raise tornado.gen.Return(result)
        finally:
            periodic_check.stop()

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        href = self.pick_http_href(td, td.get_property_forms(name))

        if href is None:
            raise ProtocolClientException("Unable to find the property form")

        http_client = tornado.httpclient.AsyncHTTPClient()
        body = json.dumps({"value": value})
        http_request = tornado.httpclient.HTTPRequest(href, method="POST", body=body, headers=self.JSON_HEADERS)
        yield http_client.fetch(http_request)

    @tornado.gen.coroutine
    def read_property(self, td, name):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        href = self.pick_http_href(td, td.get_property_forms(name))

        if href is None:
            raise ProtocolClientException("Unable to find the property form")

        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="GET")
        response = yield http_client.fetch(http_request)

        raise tornado.gen.Return(json.loads(response.body).get("value"))

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        href = self.pick_http_href(td, td.get_event_forms(name))

        if href is None:
            raise ProtocolClientException("Unable to find the event subscription form")

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

        href = self.pick_http_href(td, td.get_property_forms(name), rel=InteractionVerbs.OBSERVE_PROPERTY)

        if href is None:
            raise ProtocolClientException("Unable to find the property subscription form")

        def subscribe(observer):
            """Subscription function to observe property updates using the HTTP protocol."""

            state = {"active": True}

            def on_response(ft):
                try:
                    response = ft.result()
                    value = json.loads(response.body).get("value")
                    init = PropertyChangeEventInit(name=name, value=value)
                    observer.on_next(PropertyChangeEmittedEvent(init=init))
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

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
