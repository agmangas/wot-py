#!/usr/bin/env python
# -*- coding: utf-8 -*-

import six
import tornado.concurrent
import tornado.gen
import tornado.ioloop
import tornado.websocket

from wotpy.td.description import ThingDescription
from wotpy.wot.consumed import ConsumedThing


def test_read_property(websocket_servient):
    """Properties may be retrieved on ConsumedThings."""

    servient = websocket_servient.pop("servient")
    exposed_thing = websocket_servient.pop("exposed_thing")
    td = ThingDescription.from_thing(exposed_thing.thing)
    consumed_thing = ConsumedThing(servient=servient, td=td)

    @tornado.gen.coroutine
    def test_coroutine():
        prop_name = next(six.iterkeys(td.properties))

        result_exposed = yield exposed_thing.read_property(prop_name)
        result_consumed = yield consumed_thing.read_property(prop_name)

        assert result_consumed == result_exposed

    tornado.ioloop.IOLoop.current().run_sync(test_coroutine)
