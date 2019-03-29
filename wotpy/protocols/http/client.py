#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain the client logic for the HTTP protocol.
"""

import json
import logging
import time

import tornado.concurrent
import tornado.gen
import tornado.httpclient
import tornado.ioloop
from rx import Observable
from six.moves.urllib import parse
from tornado.simple_httpclient import HTTPTimeoutError

from wotpy.protocols.client import BaseProtocolClient
from wotpy.protocols.enums import Protocols, InteractionVerbs
from wotpy.protocols.exceptions import FormNotFoundException, ClientRequestTimeout
from wotpy.protocols.http.enums import HTTPSchemes
from wotpy.protocols.utils import is_scheme_form
from wotpy.utils.utils import handle_observer_finalization
from wotpy.wot.events import EmittedEvent, PropertyChangeEmittedEvent, PropertyChangeEventInit


class HTTPClient(BaseProtocolClient):
    """Implementation of the protocol client interface for the HTTP protocol."""

    JSON_HEADERS = {"Content-Type": "application/json"}
    DEFAULT_CON_TIMEOUT = 60
    DEFAULT_REQ_TIMEOUT = 60

    def __init__(self, connect_timeout=DEFAULT_CON_TIMEOUT, request_timeout=DEFAULT_REQ_TIMEOUT):
        self._connect_timeout = connect_timeout
        self._request_timeout = request_timeout
        self._logr = logging.getLogger(__name__)
        super(HTTPClient, self).__init__()

    @classmethod
    def pick_http_href(cls, td, forms, op=None):
        """Picks the most appropriate HTTP form href from the given list of forms."""

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

        form_https = find_href(HTTPSchemes.HTTPS)

        return form_https if form_https is not None else find_href(HTTPSchemes.HTTP)

    @property
    def protocol(self):
        """Protocol of this client instance.
        A member of the Protocols enum."""

        return Protocols.HTTP

    @property
    def connect_timeout(self):
        """Returns the default connection timeout for all HTTP requests."""

        return self._connect_timeout

    @property
    def request_timeout(self):
        """Returns the default request timeout for all HTTP requests."""

        return self._request_timeout

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
    def invoke_action(self, td, name, input_value, timeout=None):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        con_timeout = timeout if timeout else self._connect_timeout
        req_timeout = timeout if timeout else self._request_timeout

        now = time.time()

        href = self.pick_http_href(td, td.get_action_forms(name))

        if href is None:
            raise FormNotFoundException()

        body = json.dumps({"input": input_value})
        http_client = tornado.httpclient.AsyncHTTPClient()

        try:
            http_request = tornado.httpclient.HTTPRequest(
                href, method="POST",
                body=body,
                headers=self.JSON_HEADERS,
                connect_timeout=con_timeout,
                request_timeout=req_timeout)
        except HTTPTimeoutError:
            raise ClientRequestTimeout

        response = yield http_client.fetch(http_request)
        invocation_url = json.loads(response.body).get("invocation")

        @tornado.gen.coroutine
        def check_invocation():
            parsed = parse.urlparse(href)

            invoc_href = "{}://{}/{}".format(
                parsed.scheme,
                parsed.netloc,
                invocation_url.lstrip("/"))

            invoc_http_req = tornado.httpclient.HTTPRequest(
                invoc_href, method="GET",
                connect_timeout=con_timeout,
                request_timeout=req_timeout)

            self._logr.debug("Checking invocation: {}".format(invocation_url))

            try:
                invoc_res = yield http_client.fetch(invoc_http_req)
            except HTTPTimeoutError:
                self._logr.debug("Timeout checking invocation: {}".format(invocation_url))
                raise tornado.gen.Return((False, None))

            status = json.loads(invoc_res.body)

            if status.get("done") is False:
                raise tornado.gen.Return((False, None))

            if status.get("error") is not None:
                raise tornado.gen.Return((True, Exception(status.get("error"))))
            else:
                raise tornado.gen.Return((True, tornado.gen.Return(status.get("result"))))

        while True:
            done, result = yield check_invocation()

            if done:
                raise result
            elif timeout and (time.time() - now) > timeout:
                raise ClientRequestTimeout

    @tornado.gen.coroutine
    def write_property(self, td, name, value, timeout=None):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        con_timeout = timeout if timeout else self._connect_timeout
        req_timeout = timeout if timeout else self._request_timeout

        href = self.pick_http_href(td, td.get_property_forms(name))

        if href is None:
            raise FormNotFoundException()

        http_client = tornado.httpclient.AsyncHTTPClient()
        body = json.dumps({"value": value})

        try:
            http_request = tornado.httpclient.HTTPRequest(
                href, method="PUT", body=body,
                headers=self.JSON_HEADERS,
                connect_timeout=con_timeout,
                request_timeout=req_timeout)
        except HTTPTimeoutError:
            raise ClientRequestTimeout

        yield http_client.fetch(http_request)

    @tornado.gen.coroutine
    def read_property(self, td, name, timeout=None):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        con_timeout = timeout if timeout else self._connect_timeout
        req_timeout = timeout if timeout else self._request_timeout

        href = self.pick_http_href(td, td.get_property_forms(name))

        if href is None:
            raise FormNotFoundException()

        http_client = tornado.httpclient.AsyncHTTPClient()

        try:
            http_request = tornado.httpclient.HTTPRequest(
                href, method="GET",
                connect_timeout=con_timeout,
                request_timeout=req_timeout)
        except HTTPTimeoutError:
            raise ClientRequestTimeout

        response = yield http_client.fetch(http_request)

        raise tornado.gen.Return(json.loads(response.body).get("value"))

    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        href = self.pick_http_href(td, td.get_event_forms(name))

        if href is None:
            raise FormNotFoundException()

        def subscribe(observer):
            """Subscription function to observe events using the HTTP protocol."""

            state = {"active": True}

            @handle_observer_finalization(observer)
            @tornado.gen.coroutine
            def callback():
                http_client = tornado.httpclient.AsyncHTTPClient()
                http_request = tornado.httpclient.HTTPRequest(href, method="GET")

                while state["active"]:
                    try:
                        response = yield http_client.fetch(http_request)
                        payload = json.loads(response.body).get("payload")
                        observer.on_next(EmittedEvent(init=payload, name=name))
                    except HTTPTimeoutError:
                        pass

            def unsubscribe():
                state["active"] = False

            tornado.ioloop.IOLoop.current().add_callback(callback)

            return unsubscribe

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        href = self.pick_http_href(td, td.get_property_forms(name), op=InteractionVerbs.OBSERVE_PROPERTY)

        if href is None:
            raise FormNotFoundException()

        def subscribe(observer):
            """Subscription function to observe property updates using the HTTP protocol."""

            state = {"active": True}

            @handle_observer_finalization(observer)
            @tornado.gen.coroutine
            def callback():
                http_client = tornado.httpclient.AsyncHTTPClient()
                http_request = tornado.httpclient.HTTPRequest(href, method="GET")

                while state["active"]:
                    try:
                        response = yield http_client.fetch(http_request)
                        value = json.loads(response.body).get("value")
                        init = PropertyChangeEventInit(name=name, value=value)
                        observer.on_next(PropertyChangeEmittedEvent(init=init))
                    except HTTPTimeoutError:
                        pass

            def unsubscribe():
                state["active"] = False

            tornado.ioloop.IOLoop.current().add_callback(callback)

            return unsubscribe

        # noinspection PyUnresolvedReferences
        return Observable.create(subscribe)

    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError
