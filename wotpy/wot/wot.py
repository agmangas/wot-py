#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that serves as the WoT entrypoint.
"""

import json

import six
# noinspection PyCompatibility
from concurrent.futures import ThreadPoolExecutor, Future
from tornado.httpclient import HTTPClient, HTTPRequest

from wotpy.td.serialization import JSONThingDescription
from wotpy.wot.dictionaries import ThingTemplate
from wotpy.wot.exposed import ExposedThing

DEFAULT_FETCH_TIMEOUT_SECS = 20.0


class WoT(object):
    """The WoT object is the API entry point and it is exposed by an
    implementation of the WoT Runtime. The WoT object does not expose
    properties, only methods for discovering, consuming and exposing a Thing."""

    def __init__(self, servient):
        self._servient = servient

    def discover(self, thing_filter):
        """Starts the discovery process that will provide ConsumedThing
        objects that match the optional argument ThingFilter."""

        raise NotImplementedError()

    @classmethod
    def fetch(cls, url, timeout_secs=None):
        """Accepts an url argument and returns a Future
        that resolves with a Thing Description string."""

        timeout_secs = timeout_secs or DEFAULT_FETCH_TIMEOUT_SECS

        def fetch_td():
            http_client = HTTPClient()
            http_request = HTTPRequest(url, request_timeout=timeout_secs)
            http_response = http_client.fetch(http_request)
            td_doc = json.loads(http_response.body)
            JSONThingDescription.validate(td_doc)
            http_client.close()
            return json.dumps(td_doc)

        executor = ThreadPoolExecutor(max_workers=1)
        future_td = executor.submit(fetch_td)
        executor.shutdown(wait=False)

        return future_td

    def consume(self, td):
        """Accepts a thing description string argument and returns a
        ConsumedThing object instantiated based on that description."""

        raise NotImplementedError()

    def produce(self, model):
        """Accepts a model argument of type ThingModel and returns an ExposedThing
        object, locally created based on the provided initialization parameters."""

        assert isinstance(model, six.string_types) or isinstance(model, ThingTemplate)

        if isinstance(model, six.string_types):
            td_doc = json.loads(model)
            exposed_thing = ExposedThing.from_description(servient=self._servient, doc=td_doc)
        else:
            exposed_thing = ExposedThing.from_name(servient=self._servient, name=model.name)

        self._servient.add_exposed_thing(exposed_thing)

        return exposed_thing

    def produce_from_url(self, url, timeout_secs=None):
        """Return a Future that resolves to an ExposedThing created
        from the thing description retrieved from the given URL."""

        future_thing = Future()

        def build_exposed_thing(ft):
            try:
                td_str = ft.result()
                td_doc = json.loads(td_str)
                exp_thing = ExposedThing.from_description(servient=self._servient, doc=td_doc)
                future_thing.set_result(exp_thing)
            except Exception as ex:
                future_thing.set_exception(ex)

        future_td = self.fetch(url, timeout_secs=timeout_secs)
        future_td.add_done_callback(build_exposed_thing)

        return future_thing
