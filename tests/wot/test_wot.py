#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import logging
import random

# noinspection PyPackageRequirements
import pytest
import tornado.gen
import tornado.ioloop
import tornado.testing
import tornado.web
# noinspection PyCompatibility
from concurrent.futures import Future
# noinspection PyPackageRequirements
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from tests.wot.utils import assert_exposed_thing_equal
from wotpy.td.semantic import ThingSemanticContextEntry
from wotpy.wot.dictionaries import ThingTemplate, SemanticType, SemanticMetadata
from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT


def test_produce_td():
    """Things can be produced from thing descriptions serialized to JSON-LD string."""

    td_str = json.dumps(TD_EXAMPLE)
    thing_name = TD_EXAMPLE.get("name")

    servient = Servient()
    wot = WoT(servient=servient)

    exp_thing = wot.produce(td_str)

    assert servient.get_exposed_thing(thing_name)
    assert exp_thing.name == thing_name
    assert len(exp_thing.thing.interactions) == len(TD_EXAMPLE.get("interaction"))


def test_produce_thing_template():
    """Things can be produced from ThingTemplate instances."""

    fake = Faker()

    thing_name = fake.pystr()

    ctx = fake.url()
    ctx_type = fake.pystr()
    ctx_meta_name = fake.pystr()
    ctx_meta_val = fake.pystr()

    sem_type = SemanticType(name=ctx_type, context=ctx)
    sem_meta_type = SemanticType(name=ctx_meta_name, context=ctx)
    sem_meta = SemanticMetadata(semantic_type=sem_meta_type, value=ctx_meta_val)

    thing_template = ThingTemplate(name=thing_name, semantic_types=[sem_type], metadata=[sem_meta])

    servient = Servient()
    wot = WoT(servient=servient)

    exp_thing = wot.produce(thing_template)

    assert servient.get_exposed_thing(thing_name)
    assert exp_thing.name == thing_name
    assert ctx_meta_name in exp_thing.thing.semantic_metadata.items
    assert exp_thing.thing.semantic_metadata.items[ctx_meta_name] == ctx_meta_val
    assert ctx_type in exp_thing.thing.semantic_types.items
    assert ThingSemanticContextEntry(ctx) in exp_thing.thing.semantic_context.context_entries


@pytest.mark.flaky(reruns=5)
def test_produce_from_url():
    """ExposedThings can be created from URLs that provide Thing Description documents."""

    fake = Faker()

    # noinspection PyAbstractClass
    class TDHandler(tornado.web.RequestHandler):
        """Dummy handler to fetch a JSON-serialized TD document."""

        def get(self):
            self.write(TD_EXAMPLE)

    app = tornado.web.Application([(r"/", TDHandler)])
    app_port = random.randint(20000, 40000)
    app.listen(app_port)

    url_valid = "http://localhost:{}/".format(app_port)
    url_error = "http://localhost:{}/{}".format(app_port, fake.pystr())

    future_valid = Future()
    future_error = Future()

    servient = Servient()
    wot = WoT(servient=servient)
    io_loop = tornado.ioloop.IOLoop.current()

    @tornado.gen.coroutine
    def from_url(url, fut, timeout_secs=2.0):
        try:
            exp_thing = yield wot.produce_from_url(url, timeout_secs=timeout_secs)
            fut.set_result(exp_thing)
        except Exception as ex:
            fut.set_result(ex)

    @tornado.gen.coroutine
    def stop_loop():
        yield [future_valid, future_error]
        io_loop.stop()

    logging.getLogger("tornado.access").disabled = True

    io_loop.add_callback(from_url, url=url_valid, fut=future_valid)
    io_loop.add_callback(from_url, url=url_error, fut=future_error)
    io_loop.add_callback(stop_loop)
    io_loop.start()

    logging.getLogger("tornado.access").disabled = False

    assert isinstance(future_error.result(), Exception)
    assert_exposed_thing_equal(future_valid.result(), TD_EXAMPLE)
