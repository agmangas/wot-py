#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rx import Observable

from wotpy.wot.dictionaries import ThingFilter


class WoT(object):
    """WoT entrypoint."""

    def __init__(self, servient):
        self.servient = servient

    def discover(self, thing_filter):
        """Takes a ThingFilter instance and returns an Observable
        that will emit events for each discovered Thing or error."""

        assert isinstance(thing_filter, ThingFilter)
        # noinspection PyUnresolvedReferences
        return Observable.empty()

    def consume(self, url):
        """Takes a URL and returns a Future that resolves to a
        ConsumedThing that has been retrieved from the given URL."""

        pass

    def expose(self, thing_init):
        """Takes a ThingInit instance and returns a Future that resolves
        to an ExposedThing that will be hosted in the local servient."""

        pass
