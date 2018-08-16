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
from wotpy.protocols.client import BaseProtocolClient
from wotpy.td.description import ThingDescription
from wotpy.td.thing import Thing
from wotpy.wot.consumed.thing import ConsumedThing
from wotpy.wot.dictionaries.interaction import PropertyFragment, ActionFragment, EventFragment
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.servient import Servient


@pytest.fixture
def property_fragment():
    """Builds and returns a random PropertyInit."""

    return PropertyFragment({
        "label": Faker().sentence(),
        "writable": True,
        "observable": True,
        "type": "string"
    })


@pytest.fixture
def event_fragment():
    """Builds and returns a random EventInit."""

    return EventFragment({
        "label": Faker().sentence(),
        "type": "string",
        "value": Faker().sentence()
    })


@pytest.fixture
def action_fragment():
    """Builds and returns a random ActionInit."""

    return ActionFragment({
        "label": Faker().sentence(),
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
    def invoke_action(self, td, name, input_value):
        result = yield self._exp_thing.invoke_action(name, input_value)
        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def write_property(self, td, name, value):
        yield self._exp_thing.write_property(name, value)

    @tornado.gen.coroutine
    def read_property(self, td, name):
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

    exp_thing = ExposedThing(
        servient=Servient(),
        thing=Thing(id=uuid.uuid4().urn))

    @tornado.gen.coroutine
    def lower(parameters):
        input_value = parameters.get("input")
        yield tornado.gen.sleep(0)
        raise tornado.gen.Return(str(input_value).lower())

    exp_thing.add_property(uuid.uuid4().hex, property_fragment())
    exp_thing.add_action(uuid.uuid4().hex, action_fragment(), lower)
    exp_thing.add_event(uuid.uuid4().hex, event_fragment())

    servient = Servient()
    servient.select_client = MagicMock(return_value=ExposedThingProxyClient(exp_thing))
    td = ThingDescription.from_thing(exp_thing.thing)

    return {
        "consumed_thing": ConsumedThing(servient=servient, td=td),
        "exposed_thing": exp_thing
    }
