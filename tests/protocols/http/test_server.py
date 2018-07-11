#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import six
import tornado.gen
import tornado.httpclient
import tornado.ioloop
from faker import Faker
from six.moves.urllib import parse


def _get_property_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property read/write href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("localhost", prop)
    return next(item.href for item in prop_forms if item.rel is None)


def _get_property_observe_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property subscription href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("localhost", prop)
    return next(item.href for item in prop_forms if item.rel == "observeProperty")


def test_property_get(http_server):
    """Properties exposed in an HTTP server can be read with an HTTP GET request."""

    exposed_thing = next(http_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    href = _get_property_href(exposed_thing, prop_name, http_server)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_value = Faker().pyint()
        yield exposed_thing.properties[prop_name].set(prop_value)
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="GET")
        response = yield http_client.fetch(http_request)

        assert json.loads(response.body).get("value") == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def _test_property_set(server, body, prop_value, headers=None):
    """Helper function to test Property updates over HTTP."""

    exposed_thing = next(server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    href = _get_property_href(exposed_thing, prop_name, server)

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="POST", body=body, headers=headers)
        response = yield http_client.fetch(http_request)
        value = yield exposed_thing.properties[prop_name].get()

        assert response.rethrow() is None
        assert value == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_property_set_form_urlencoded(http_server):
    """Properties exposed in an HTTP server can be
    updated with an application/x-www-form-urlencoded HTTP POST request."""

    prop_value = Faker().pyint()
    body = parse.urlencode({"value": prop_value})
    _test_property_set(http_server, body, str(prop_value))


def test_property_set_json(http_server):
    """Properties exposed in an HTTP server can be
    updated with an application/json HTTP POST request."""

    prop_value = Faker().pyint()
    body = json.dumps({"value": prop_value})
    _test_property_set(http_server, body, prop_value, headers={"Content-Type": "application/json"})


def test_property_subscribe(http_server):
    """Properties exposed in an HTTP server can be subscribed to with an HTTP GET request."""

    exposed_thing = next(http_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    href = _get_property_observe_href(exposed_thing, prop_name, http_server)

    init_value = Faker().pyint()
    prop_value = Faker().pyint()

    assert init_value != prop_value

    @tornado.gen.coroutine
    def set_property():
        yield exposed_thing.properties[prop_name].set(prop_value)

    @tornado.gen.coroutine
    def test_coroutine():
        yield exposed_thing.properties[prop_name].set(init_value)

        periodic_set = tornado.ioloop.PeriodicCallback(set_property, 10)
        periodic_set.start()

        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="GET")
        response = yield http_client.fetch(http_request)

        periodic_set.stop()

        assert json.loads(response.body).get("value") == prop_value

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
