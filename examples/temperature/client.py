#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A simple Temperature Thing that serves as an
example for how to use the WotPy servient.
"""

import json
import logging

import six
import tornado.gen
import tornado.ioloop
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from wotpy.wot.servient import Servient

CATALOGUE_URL = "http://localhost:9292"
NAME_EVENT_TEMP_HIGH = "high-temperature"

logging.basicConfig()
LOGGER = logging.getLogger("temperature-client")
LOGGER.setLevel(logging.INFO)


@tornado.gen.coroutine
def fetch_td_url():
    """Yields the URL of the Thing Description document."""

    LOGGER.info("Fetching TD URL")

    http_client = AsyncHTTPClient()
    http_request = HTTPRequest(CATALOGUE_URL)

    http_response = yield http_client.fetch(http_request)

    tds_map = json.loads(http_response.body)
    td_path = next(six.itervalues(tds_map))
    td_url = "{}/{}".format(CATALOGUE_URL, td_path.strip("/"))

    LOGGER.info("TD URL: {}".format(td_url))

    raise tornado.gen.Return(td_url)


@tornado.gen.coroutine
def main():
    """Consumes the Thing Description document and starts listening for events."""

    wot = yield Servient().start()

    td_url = yield fetch_td_url()
    consumed_thing = yield wot.consume_from_url(td_url)

    def on_next_event(ev):
        LOGGER.info("Event {} payload: {}".format(NAME_EVENT_TEMP_HIGH, ev.data))

    subscription = consumed_thing.events[NAME_EVENT_TEMP_HIGH].subscribe(on_next_event)

    LOGGER.info("Listening for event: {}".format(NAME_EVENT_TEMP_HIGH))

    yield tornado.gen.sleep(60)

    subscription.dispose()


if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
