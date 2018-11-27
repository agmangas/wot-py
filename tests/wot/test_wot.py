#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import random
import uuid

import pytest
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.testing
import tornado.web
from faker import Faker
from rx.concurrency import IOLoopScheduler

from tests.td_examples import TD_EXAMPLE
from tests.wot.utils import assert_exposed_thing_equal
from wotpy.wot.dictionaries.filter import ThingFilterDict
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
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

    thing_template = ThingFragment({
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


TD_DICT_01 = {
    "id": uuid.uuid4().urn,
    "name": Faker().pystr(),
    "security": [{"scheme": "nosec"}],
    "version": {"instance": "1.2.1"},
    "properties": {
        "status": {
            "description": Faker().pystr(),
            "type": "string"
        }
    }
}

TD_DICT_02 = {
    "id": uuid.uuid4().urn,
    "version": {"instance": "2.0.0"},
    "actions": {
        "toggle": {
            "output": {"type": "boolean"}
        }
    }
}


def assert_equal_tds(one, other):
    """Asserts that both TDs are equal."""

    one = ThingDescription(one) if not isinstance(one, ThingDescription) else one
    other = ThingDescription(other) if not isinstance(other, ThingDescription) else other
    assert one.to_dict() == other.to_dict()


def test_discovery_any():
    """All TDs contained in the Servient are returned when the Thing filter is empty."""

    servient = Servient()
    wot = WoT(servient=servient)
    wot.produce(ThingFragment(TD_DICT_01))
    wot.produce(ThingFragment(TD_DICT_02))

    @tornado.gen.coroutine
    def test_coroutine():
        future_done, found = tornado.concurrent.Future(), []

        def on_next(td_str):
            found.append(ThingDescription(td_str))

            if len(found) == 2 and not future_done.done():
                future_done.set_result(True)

        thing_filter = ThingFilterDict()
        observable = wot.discover(thing_filter)
        subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

        yield future_done

        assert len(found) == 2
        assert_equal_tds(next(item.to_dict() for item in found if item.id == TD_DICT_01["id"]), TD_DICT_01)
        assert_equal_tds(next(item.to_dict() for item in found if item.id == TD_DICT_02["id"]), TD_DICT_02)

        subscription.dispose()

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)


def test_discovery_filter_fragment():
    """The Thing filter fragment attribute enables discovering Things by matching TD fields."""

    servient = Servient()
    wot = WoT(servient=servient)
    wot.produce(ThingFragment(TD_DICT_01))
    wot.produce(ThingFragment(TD_DICT_02))

    def first(thing_filter):
        """Returns the first TD discovery for the given Thing filter."""

        @tornado.gen.coroutine
        def discover_first():
            ret, future_done = [], tornado.concurrent.Future()

            def on_next(td_str):
                ret.append(ThingDescription(td_str))

                if not future_done.done():
                    future_done.set_result(True)

            observable = wot.discover(thing_filter)
            subscription = observable.subscribe_on(IOLoopScheduler()).subscribe(on_next)

            yield future_done

            subscription.dispose()

            assert len(ret)

            raise tornado.gen.Return(ret[0])

        return tornado.ioloop.IOLoop.current().run_sync(discover_first)

    assert_equal_tds(first(ThingFilterDict(fragment={"name": TD_DICT_01.get("name")})), TD_DICT_01)
    assert_equal_tds(first(ThingFilterDict(fragment={"version": {"instance": "2.0.0"}})), TD_DICT_02)
    assert_equal_tds(first(ThingFilterDict(fragment={"id": TD_DICT_02.get("id")})), TD_DICT_02)
