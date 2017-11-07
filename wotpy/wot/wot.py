#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyCompatibility
from concurrent.futures import Future
from rx import Observable

from wotpy.wot.exposed import ExposedThing


class WoT(object):
    """WoT entrypoint."""

    def __init__(self, servient):
        self._servient = servient

    def discover(self, thing_filter):
        """Takes a ThingFilter instance and returns an Observable
        that will emit events for each discovered Thing or error."""

        # noinspection PyUnresolvedReferences
        return Observable.empty()

    def consume(self, url):
        """Takes a URL and returns a Future that resolves to a
        ConsumedThing that has been retrieved from the given URL."""

        future_consumed = Future()
        future_consumed.set_exception(NotImplementedError())

        return future_consumed

    def expose(self, thing_init):
        """Takes a ThingInit instance and returns a Future that resolves
        to an ExposedThing that will be hosted in the local servient."""

        future_exposed = Future()

        if thing_init.description:
            exp_thing = ExposedThing.from_description(
                servient=self._servient,
                doc=thing_init.description,
                name=thing_init.name)
            future_exposed.set_result(exp_thing)
        elif thing_init.url:
            future_exposed = ExposedThing.from_url(
                servient=self._servient,
                url=thing_init.url,
                name=thing_init.name)
        else:
            exp_thing = ExposedThing.from_name(
                servient=self._servient,
                name=thing_init.name)
            future_exposed.set_result(exp_thing)

        def add_to_servient(ft):
            self._servient.add_exposed_thing(ft.result())

        future_exposed.add_done_callback(add_to_servient)

        return future_exposed
