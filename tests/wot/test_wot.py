#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random

# noinspection PyPackageRequirements
import pytest
import tornado.gen
import tornado.ioloop
import tornado.testing
import tornado.web
# noinspection PyPackageRequirements
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from tests.wot.utils import assert_exposed_thing_equal
from wotpy.wot.dictionaries.wot import ThingTemplateDict
from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT


def test_produce_model_str():
    """Things can be produced from TD documents serialized to JSON-LD string."""

    td_str = json.dumps(TD_EXAMPLE)
    thing_id = TD_EXAMPLE.get("id")

    servient = Servient()
    wot = WoT(servient=servient)

    exp_thing = wot.produce(td_str)

    assert servient.get_exposed_thing(thing_id)
    assert exp_thing.thing.id == thing_id
    assert_exposed_thing_equal(exp_thing, TD_EXAMPLE)


def test_produce_model_thing_template():
    """Things can be produced from ThingTemplate instances."""

    thing_id = Faker().url()
    thing_name = Faker().sentence()

    thing_template = ThingTemplateDict({
        "id": thing_id,
        "name": thing_name
    })

    servient = Servient()
    wot = WoT(servient=servient)

    exp_thing = wot.produce(thing_template)

    assert servient.get_exposed_thing(thing_id)
    assert exp_thing.id == thing_id
    assert exp_thing.name == thing_name


def test_produce_model_consumed_thing():
    """Things can be produced from ConsumedThing instances."""

    servient = Servient()
    wot = WoT(servient=servient)

    td_str = json.dumps(TD_EXAMPLE)
    consumed_thing = wot.consume(td_str)
    exposed_thing = wot.produce(consumed_thing)

    assert exposed_thing.id == consumed_thing.td.id
    assert exposed_thing.name == consumed_thing.td.name
    assert len(exposed_thing.properties) == len(consumed_thing.td.properties)
    assert len(exposed_thing.actions) == len(consumed_thing.td.actions)
    assert len(exposed_thing.events) == len(consumed_thing.td.events)


@pytest.mark.flaky(reruns=5)
def test_produce_from_url(td_example_tornado_app):
    """ExposedThings can be created from URLs that provide Thing Description documents."""

    app_port = random.randint(20000, 40000)
    td_example_tornado_app.listen(app_port)

    url_valid = "http://localhost:{}/".format(app_port)
    url_error = "http://localhost:{}/{}".format(app_port, Faker().pystr())

    wot = WoT(servient=Servient())

    @tornado.gen.coroutine
    def test_coroutine():
        exposed_thing = yield wot.produce_from_url(url_valid)

        assert exposed_thing.thing.id == TD_EXAMPLE.get("id")

        with pytest.raises(Exception):
            yield wot.produce_from_url(url_error)

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


@pytest.mark.flaky(reruns=5)
def test_consume_from_url(td_example_tornado_app):
    """ConsumedThings can be created from URLs that provide Thing Description documents."""

    app_port = random.randint(20000, 40000)
    td_example_tornado_app.listen(app_port)

    url_valid = "http://localhost:{}/".format(app_port)
    url_error = "http://localhost:{}/{}".format(app_port, Faker().pystr())

    wot = WoT(servient=Servient())

    @tornado.gen.coroutine
    def test_coroutine():
        consumed_thing = yield wot.consume_from_url(url_valid)

        assert consumed_thing.td.id == TD_EXAMPLE.get("id")

        with pytest.raises(Exception):
            yield wot.consume_from_url(url_error)

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
