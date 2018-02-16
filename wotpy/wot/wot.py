#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import six

from wotpy.wot.exposed import ExposedThing
from wotpy.wot.dictionaries import ThingTemplate


class WoT(object):
    """WoT entrypoint."""

    def __init__(self, servient):
        self._servient = servient

    def discover(self, thing_filter):
        """Starts the discovery process that will provide ConsumedThing
        objects that match the optional argument ThingFilter."""

        raise NotImplementedError()

    def fetch(self, url):
        """Accepts an url argument and returns a Future
        that resolves with a Thing Description string."""

        raise NotImplementedError()

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
            model.copy_annotations_to_thing(exposed_thing.thing)

        self._servient.add_exposed_thing(exposed_thing)

        return exposed_thing
