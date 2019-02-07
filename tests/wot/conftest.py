#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

import pytest
import tornado.gen
import tornado.ioloop
import tornado.web
from faker import Faker
from mock import MagicMock

from tests.td_examples import TD_EXAMPLE
from tests.utils import find_free_port
from wotpy.protocols.client import BaseProtocolClient
from wotpy.wot.consumed.thing import ConsumedThing
from wotpy.wot.dictionaries.interaction import PropertyFragmentDict, ActionFragmentDict, EventFragmentDict
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing


def _build_property_fragment():
    """Builds and returns a random Property init fragment."""

    return PropertyFragmentDict({
        "description": Faker().sentence(),
        "readOnly": False,
        "observable": True,
        "type": "string"
    })


def _build_event_fragment():
    """Builds and returns a random Event init fragment."""

    return EventFragmentDict({
        "description": Faker().sentence(),
        "data": {"type": "string"}
    })


def _build_action_fragment():
    """Builds and returns a random Action init fragment."""

    return ActionFragmentDict({
        "description": Faker().sentence(),
        "input": {
            "type": "string",
            "description": Faker().sentence()
        },
        "output": {
            "type": "string",
            "description": Faker().sentence()
        }
    })


@pytest.fixture
def property_fragment():
    """Builds and returns a random Property init fragment."""

    return _build_property_fragment()


@pytest.fixture
def action_fragment():
    """Builds and returns a random ActionInit."""

    return _build_action_fragment()


@pytest.fixture
def event_fragment():
    """Builds and returns a random EventInit."""

    return _build_event_fragment()


@pytest.fixture
def exposed_thing():
    """Builds and returns a random ExposedThing."""

    return ExposedThing(
        servient=Servient(),
        thing=Thing(id=uuid.uuid4().urn))


@pytest.fixture
def td_example_tornado_app():
    """Builds a Tornado web application with a simple handler
    that exposes the example Thing Description document."""

    # noinspection PyAbstractClass
    class TDHandler(tornado.web.RequestHandler):
        """Dummy handler to fetch a JSON-serialized TD document."""

        def get(self):
            self.write(TD_EXAMPLE)

    return tornado.web.Application([(r"/", TDHandler)])


class ExposedThingProxyClient(BaseProtocolClient):
    """Dummy Protocol Binding client implementation that
    basically serves as a proxy for a local ExposedThing object."""

    def __init__(self, exp_thing):
        self._exp_thing = exp_thing
        super(ExposedThingProxyClient, self).__init__()

    @property
    def protocol(self):
        return None

    def is_supported_interaction(self, td, name):
        return True

    @tornado.gen.coroutine
    def invoke_action(self, td, name, input_value, timeout=None):
        result = yield self._exp_thing.invoke_action(name, input_value)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def write_property(self, td, name, value, timeout=None):
        yield self._exp_thing.write_property(name, value)

    @tornado.gen.coroutine
    def read_property(self, td, name, timeout=None):
        value = yield self._exp_thing.read_property(name)
        raise tornado.gen.Return(value)

    def on_event(self, td, name):
        return self._exp_thing.on_event(name)

    def on_property_change(self, td, name):
        return self._exp_thing.on_property_change(name)

    def on_td_change(self, url):
        return self._exp_thing.on_td_change()


@pytest.fixture
def consumed_exposed_pair():
    """Returns a dict with two keys:
    * consumed_thing: A ConsumedThing instance. The Servient instance that contains this
    ConsumedThing has been patched to use the ExposedThingProxyClient Protocol Binding client.
    * exposed_thing: The ExposedThing behind the previous ConsumedThing (for assertion purposes)."""

    servient = Servient()

    exp_thing = ExposedThing(
        servient=servient,
        thing=Thing(id=uuid.uuid4().urn))

    servient.select_client = MagicMock(return_value=ExposedThingProxyClient(exp_thing))

    @tornado.gen.coroutine
    def lower(parameters):
        input_value = parameters.get("input")
        yield tornado.gen.sleep(0)
        raise tornado.gen.Return(str(input_value).lower())

    exp_thing.add_property(uuid.uuid4().hex, _build_property_fragment())
    exp_thing.add_action(uuid.uuid4().hex, _build_action_fragment(), lower)
    exp_thing.add_event(uuid.uuid4().hex, _build_event_fragment())

    td = ThingDescription.from_thing(exp_thing.thing)

    return {
        "consumed_thing": ConsumedThing(servient=servient, td=td),
        "exposed_thing": exp_thing
    }


@pytest.fixture(params=[{"catalogue_enabled": True}])
def servient(request):
    """Returns an empty WoT Servient."""

    catalogue_port = find_free_port() if request.param.get('catalogue_enabled') else None

    servient = Servient(catalogue_port=catalogue_port)

    @tornado.gen.coroutine
    def start():
        yield servient.start()

    tornado.ioloop.IOLoop.current().run_sync(start)

    yield servient

    @tornado.gen.coroutine
    def shutdown():
        yield servient.shutdown()

    tornado.ioloop.IOLoop.current().run_sync(shutdown)
