#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import json
import random
import ssl
import uuid

import pytest
import six
import tornado.gen
import tornado.httpclient
import tornado.ioloop
from faker import Faker
from six.moves.urllib import parse
from tornado.concurrent import Future

from tests.utils import find_free_port, run_test_coroutine
from wotpy.protocols.enums import InteractionVerbs
from wotpy.protocols.http.enums import HTTPSchemes
from wotpy.protocols.http.server import HTTPServer
from wotpy.wot.dictionaries.interaction import PropertyFragmentDict
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.thing import Thing

JSON_HEADERS = {"Content-Type": "application/json"}
FORM_URLENCODED_HEADERS = {"Content-Type": "application/x-www-form-urlencoded"}


def _get_property_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property read/write href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("localhost", prop)
    return next(item.href for item in prop_forms if item.op == InteractionVerbs.READ_PROPERTY)


def _get_property_observe_href(exp_thing, prop_name, server):
    """Helper function to retrieve the Property subscription href."""

    prop = exp_thing.thing.properties[prop_name]
    prop_forms = server.build_forms("localhost", prop)
    return next(item.href for item in prop_forms if item.op == InteractionVerbs.OBSERVE_PROPERTY)


def _get_action_href(exp_thing, action_name, server):
    """Helper function to retrieve the Property subscription href."""

    action = exp_thing.thing.actions[action_name]
    action_forms = server.build_forms("localhost", action)
    return next(item.href for item in action_forms if item.op == InteractionVerbs.INVOKE_ACTION)


def _get_event_observe_href(exp_thing, event_name, server):
    """Helper function to retrieve the Event subscription href."""

    event = exp_thing.thing.events[event_name]
    event_forms = server.build_forms("localhost", event)
    return next(item.href for item in event_forms if item.op == InteractionVerbs.SUBSCRIBE_EVENT)


def test_property_get(http_server):
    """Properties exposed in an HTTP server can be read with an HTTP GET request."""

    exposed_thing = next(http_server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    href = _get_property_href(exposed_thing, prop_name, http_server)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_value = Faker().pyint()
        yield exposed_thing.properties[prop_name].write(prop_value)
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="GET")
        response = yield http_client.fetch(http_request)

        assert json.loads(response.body).get("value") == prop_value

    run_test_coroutine(test_coroutine)


def _test_property_set(server, body, prop_value, headers=None):
    """Helper function to test Property updates over HTTP."""

    exposed_thing = next(server.exposed_things)
    prop_name = next(six.iterkeys(exposed_thing.thing.properties))
    href = _get_property_href(exposed_thing, prop_name, server)

    @tornado.gen.coroutine
    def test_coroutine():
        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="PUT", body=body, headers=headers)
        response = yield http_client.fetch(http_request)
        value = yield exposed_thing.properties[prop_name].read()

        assert response.rethrow() is None
        assert value == prop_value

    run_test_coroutine(test_coroutine)


def test_property_set_form_urlencoded(http_server):
    """Properties exposed in an HTTP server can be
    updated with an application/x-www-form-urlencoded HTTP PUT request."""

    prop_value = Faker().pyint()
    body = parse.urlencode({"value": prop_value})
    _test_property_set(http_server, body, str(prop_value), headers=FORM_URLENCODED_HEADERS)


def test_property_set_json(http_server):
    """Properties exposed in an HTTP server can be
    updated with an application/json HTTP PUT request."""

    prop_value = Faker().pyint()
    body = json.dumps({"value": prop_value})
    _test_property_set(http_server, body, prop_value, headers=JSON_HEADERS)


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
        yield exposed_thing.properties[prop_name].write(prop_value)

    @tornado.gen.coroutine
    def test_coroutine():
        yield exposed_thing.properties[prop_name].write(init_value)

        periodic_set = tornado.ioloop.PeriodicCallback(set_property, 10)
        periodic_set.start()

        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="GET")
        response = yield http_client.fetch(http_request)

        periodic_set.stop()

        assert json.loads(response.body).get("value") == prop_value

    run_test_coroutine(test_coroutine)


@tornado.gen.coroutine
def _test_action_run(server):
    """Helper to run Action invocation tests."""

    exposed_thing = next(server.exposed_things)
    action_name = next(six.iterkeys(exposed_thing.thing.actions))
    href = _get_action_href(exposed_thing, action_name, server)

    action_future = Future()

    @tornado.gen.coroutine
    def action_handler(parameters):
        yield action_future
        raise tornado.gen.Return(parameters.get("input") * 2)

    exposed_thing.set_action_handler(action_name, action_handler)

    input_value = Faker().pyint()
    body = json.dumps({"input": input_value})
    http_client = tornado.httpclient.AsyncHTTPClient()
    http_request = tornado.httpclient.HTTPRequest(href, method="POST", body=body, headers=JSON_HEADERS)
    response = yield http_client.fetch(http_request)
    invocation_url = json.loads(response.body).get("invocation")

    assert invocation_url is not None

    @tornado.gen.coroutine
    def fetch_invocation():
        href_invoc = "http://localhost:{}/{}".format(server.port, invocation_url.lstrip("/"))
        http_request_invoc = tornado.httpclient.HTTPRequest(href_invoc, method="GET")
        response_invoc = yield http_client.fetch(http_request_invoc)
        raise tornado.gen.Return(json.loads(response_invoc.body))

    raise tornado.gen.Return({
        "expected_result": input_value * 2,
        "fetch_invocation": fetch_invocation,
        "action_future": action_future
    })


def test_action_run_success(http_server):
    """Actions exposed in an HTTP server can be successfully invoked with an HTTP POST request."""

    @tornado.gen.coroutine
    def test_coroutine():
        action_fixtures = yield _test_action_run(http_server)
        expected_result = action_fixtures.pop("expected_result")
        fetch_invocation = action_fixtures.pop("fetch_invocation")
        action_future = action_fixtures.pop("action_future")

        tornado.ioloop.IOLoop.current().add_timeout(
            datetime.timedelta(seconds=random.random()),
            lambda: action_future.set_result(True))

        invocation = yield fetch_invocation()

        assert invocation.get("done") is True
        assert invocation.get("result") == expected_result
        assert invocation.get("error", None) is None

    run_test_coroutine(test_coroutine)


def test_action_run_error(http_server):
    """Actions exposed in an HTTP server can raise errors."""

    @tornado.gen.coroutine
    def test_coroutine():
        action_fixtures = yield _test_action_run(http_server)
        fetch_invocation = action_fixtures.pop("fetch_invocation")
        action_future = action_fixtures.pop("action_future")

        ex_message = Faker().sentence()

        tornado.ioloop.IOLoop.current().add_timeout(
            datetime.timedelta(seconds=random.random()),
            lambda: action_future.set_exception(Exception(ex_message)))

        invocation = yield fetch_invocation()

        assert invocation.get("done") is True
        assert invocation.get("result", None) is None
        assert ex_message in invocation.get("error")

    run_test_coroutine(test_coroutine)


def test_event_subscribe(http_server):
    """Events exposed in an HTTP server can be subscribed to with an HTTP GET request."""

    exposed_thing = next(http_server.exposed_things)
    event_name = next(six.iterkeys(exposed_thing.thing.events))
    href = _get_event_observe_href(exposed_thing, event_name, http_server)

    fake = Faker()
    payload = {fake.pystr(): random.choice([fake.pystr(), fake.pyint()]) for _ in range(5)}

    @tornado.gen.coroutine
    def emit_event():
        yield exposed_thing.emit_event(event_name, payload)

    @tornado.gen.coroutine
    def test_coroutine():
        periodic_set = tornado.ioloop.PeriodicCallback(emit_event, 10)
        periodic_set.start()

        http_client = tornado.httpclient.AsyncHTTPClient()
        http_request = tornado.httpclient.HTTPRequest(href, method="GET")
        response = yield http_client.fetch(http_request)

        periodic_set.stop()

        assert json.loads(response.body).get("payload") == payload

    run_test_coroutine(test_coroutine)


def test_ssl_context(self_signed_ssl_context):
    """An SSL context can be passed to the HTTP server to enable encryption."""

    exposed_thing = ExposedThing(servient=Servient(), thing=Thing(id=uuid.uuid4().urn))

    prop_name = uuid.uuid4().hex

    exposed_thing.add_property(prop_name, PropertyFragmentDict({
        "type": "string",
        "observable": True
    }), value=Faker().pystr())

    port = find_free_port()

    server = HTTPServer(port=port, ssl_context=self_signed_ssl_context)
    server.add_exposed_thing(exposed_thing)

    href = _get_property_href(exposed_thing, prop_name, server)

    assert HTTPSchemes.HTTPS in href

    @tornado.gen.coroutine
    def test_coroutine():
        yield server.start()

        prop_value = Faker().pystr()
        yield exposed_thing.properties[prop_name].write(prop_value)
        http_client = tornado.httpclient.AsyncHTTPClient()

        with pytest.raises(ssl.SSLError):
            yield http_client.fetch(tornado.httpclient.HTTPRequest(href, method="GET"))

        http_request = tornado.httpclient.HTTPRequest(href, method="GET", validate_cert=False)
        response = yield http_client.fetch(http_request)

        assert json.loads(response.body).get("value") == prop_value

        yield server.stop()

    run_test_coroutine(test_coroutine)
