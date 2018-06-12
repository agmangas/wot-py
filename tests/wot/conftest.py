#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

# noinspection PyPackageRequirements
import pytest
import tornado.web
# noinspection PyPackageRequirements
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from wotpy.td.thing import Thing
from wotpy.wot.dictionaries import PropertyInit, ActionInit, EventInit
from wotpy.wot.exposed import ExposedThing
from wotpy.wot.servient import Servient


@pytest.fixture
def property_init():
    """Builds and returns a random PropertyInit."""

    return PropertyInit({
        "label": Faker().sentence(),
        "writable": True,
        "observable": True,
        "type": "string"
    })


@pytest.fixture
def event_init():
    """Builds and returns a random EventInit."""

    return EventInit({
        "label": Faker().sentence(),
        "type": "string"
    })


@pytest.fixture
def action_init():
    """Builds and returns a random ActionInit."""

    return ActionInit({
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
