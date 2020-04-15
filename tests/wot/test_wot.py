#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import uuid
import warnings

import pytest
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.testing
import tornado.web
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from tests.utils import find_free_port, run_test_coroutine
from tests.wot.utils import assert_exposed_thing_equal
from wotpy.support import is_dnssd_supported
from wotpy.wot.dictionaries.filter import ThingFilterDict
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.enums import DiscoveryMethod
from wotpy.wot.servient import Servient
from wotpy.wot.td import ThingDescription
from wotpy.wot.wot import WoT

TIMEOUT_DISCOVER = 5


def test_produce_model_str():
    """Things can be produced from TD documents serialized to JSON-LD string."""

    td_str = json.dumps(TD_EXAMPLE)
    thing_id = TD_EXAMPLE.get("id")

    servient = Servient()
    wot = WoT(servient=servient)
    
    assert wot.servient is servient

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


def test_produce_from_url(td_example_tornado_app):
    """ExposedThings can be created from URLs that provide Thing Description documents."""

    app_port = find_free_port()
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

    run_test_coroutine(test_coroutine)


def test_consume_from_url(td_example_tornado_app):
    """ConsumedThings can be created from URLs that provide Thing Description documents."""

    app_port = find_free_port()
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

    run_test_coroutine(test_coroutine)


TD_DICT_01 = {
    "id": uuid.uuid4().urn,
    "name": Faker().pystr(),
    "security": [{"scheme": "psk"}],
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


def assert_equal_td_sequences(tds, td_dicts):
    """Asserts that the given sequences ot TDs and TD dicts are equal."""

    assert len(tds) == len(td_dicts)

    for td_dict in td_dicts:
        td_match = next(td.to_dict() for td in tds if td.id == td_dict["id"])
        assert_equal_tds(td_match, td_dict)


def test_discovery_method_local():
    """All TDs contained in the Servient are returned when using the local
    discovery method without defining the fragment nor the query fields."""

    servient = Servient(dnssd_enabled=False)
    wot = WoT(servient=servient)
    wot.produce(ThingFragment(TD_DICT_01))
    wot.produce(ThingFragment(TD_DICT_02))

    future_done, found = tornado.concurrent.Future(), []

    def resolve():
        len(found) == 2 and not future_done.done() and future_done.set_result(True)

    @tornado.gen.coroutine
    def test_coroutine():
        thing_filter = ThingFilterDict(method=DiscoveryMethod.LOCAL)
        observable = wot.discover(thing_filter)

        subscription = observable.subscribe(
            on_next=lambda td_str: found.append(ThingDescription(td_str)) or resolve())

        yield future_done

        assert_equal_td_sequences(found, [TD_DICT_01, TD_DICT_02])

        subscription.dispose()

    run_test_coroutine(test_coroutine)


@pytest.mark.skipif(not is_dnssd_supported(), reason="Only for platforms that support DNS-SD")
def test_discovery_method_multicast_dnssd():
    """Things can be discovered usin the multicast method supported by DNS-SD."""

    catalogue_port_01 = find_free_port()
    catalogue_port_02 = find_free_port()

    instance_name_01 = "servient-01-{}".format(Faker().pystr())
    instance_name_02 = "servient-02-{}".format(Faker().pystr())

    servient_01 = Servient(
        catalogue_port=catalogue_port_01,
        dnssd_enabled=True,
        dnssd_instance_name=instance_name_01)

    servient_02 = Servient(
        catalogue_port=catalogue_port_02,
        dnssd_enabled=True,
        dnssd_instance_name=instance_name_02)

    future_done, found = tornado.concurrent.Future(), []

    def resolve():
        len(found) == 2 and not future_done.done() and future_done.set_result(True)

    @tornado.gen.coroutine
    def test_coroutine():
        wot_01 = yield servient_01.start()
        wot_02 = yield servient_02.start()

        wot_01.produce(ThingFragment(TD_DICT_01)).expose()
        wot_01.produce(ThingFragment(TD_DICT_02)).expose()

        thing_filter = ThingFilterDict(method=DiscoveryMethod.MULTICAST)

        observable = wot_02.discover(thing_filter, dnssd_find_kwargs={
            "min_results": 1,
            "timeout": 5
        })

        subscription = observable.subscribe(
            on_next=lambda td_str: found.append(ThingDescription(td_str)) or resolve())

        yield future_done

        assert_equal_td_sequences(found, [TD_DICT_01, TD_DICT_02])

        subscription.dispose()

        yield servient_01.shutdown()
        yield servient_02.shutdown()

    run_test_coroutine(test_coroutine)


@pytest.mark.skipif(is_dnssd_supported(), reason="Only for platforms that do not support DNS-SD")
def test_discovery_method_multicast_dnssd_unsupported():
    """Attempting to discover other Things using multicast
    DNS-SD in an unsupported platform raises a warning."""

    servient = Servient(catalogue_port=None, dnssd_enabled=True)

    @tornado.gen.coroutine
    def test_coroutine():
        wot = yield servient.start()

        with warnings.catch_warnings(record=True) as warns:
            wot.discover(ThingFilterDict(method=DiscoveryMethod.MULTICAST))
            assert len(warns)

        yield servient.shutdown()

    run_test_coroutine(test_coroutine)


def test_discovery_fragment():
    """The Thing filter fragment attribute enables discovering Things by matching TD fields."""

    servient = Servient(dnssd_enabled=False)
    wot = WoT(servient=servient)
    wot.produce(ThingFragment(TD_DICT_01))
    wot.produce(ThingFragment(TD_DICT_02))

    def first(thing_filter):
        """Returns the first TD discovery for the given Thing filter."""

        future_done, found = tornado.concurrent.Future(), []

        def resolve():
            not future_done.done() and future_done.set_result(True)

        @tornado.gen.coroutine
        def discover_first():
            observable = wot.discover(thing_filter)

            subscription = observable.subscribe(
                on_next=lambda td_str: found.append(ThingDescription(td_str)) or resolve())

            yield future_done

            subscription.dispose()

            assert len(found)

            raise tornado.gen.Return(found[0])

        return tornado.ioloop.IOLoop.current().run_sync(discover_first, timeout=TIMEOUT_DISCOVER)

    fragment_td_pairs = [
        ({"name": TD_DICT_01.get("name")}, TD_DICT_01),
        ({"version": {"instance": "2.0.0"}}, TD_DICT_02),
        ({"id": TD_DICT_02.get("id")}, TD_DICT_02),
        ({"security": [{"scheme": "psk"}]}, TD_DICT_01)
    ]

    for fragment, td_expected in fragment_td_pairs:
        td_found = first(ThingFilterDict(method=DiscoveryMethod.LOCAL, fragment=fragment))
        assert_equal_tds(td_found, td_expected)
