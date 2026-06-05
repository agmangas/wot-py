#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Classes that represent the JSON and JSON-LD serialization formats of a Thing Description document.
"""

import json

import jsonschema

from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.thing import Thing
from wotpy.wot.validation import SCHEMA_THING, InvalidDescription


class ThingDescription(object):
    """Class that represents a Thing Description document.
    Contains logic to validate and transform a Thing to a serialized TD and vice versa.
    """

    def __init__(self, doc):
        """Constructor.
        Validates that the document conforms to the TD schema."""

        self._doc = json.loads(doc) if isinstance(doc, (str, bytes)) else doc
        self._thing_fragment = ThingFragment(self._doc)

        self.validate(doc=self._thing_fragment.to_dict())

    @classmethod
    def validate(cls, doc):
        """Validates the given Thing Description document against its schema.
        Raises ValidationError if validation fails."""

        try:
            jsonschema.validate(doc, SCHEMA_THING)
        except (jsonschema.ValidationError, TypeError) as ex:
            raise InvalidDescription(str(ex)) from ex

    @classmethod
    def from_thing(cls, thing):
        """Builds an instance of a JSON-serialized Thing Description from a Thing object."""

        return ThingDescription(thing.thing_fragment.to_dict())

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal ThingFragment before propagating the exception."""

        return getattr(self._thing_fragment, name)

    def to_dict(self):
        """Returns the JSON Thing Description as a dict."""

        return self._thing_fragment.to_dict()

    def to_str(self):
        """Returns the JSON Thing Description as a string."""

        return json.dumps(self._thing_fragment.to_dict())

    def to_thing_fragment(self):
        """Returns a ThingFragment dictionary built from this TD."""

        return self._thing_fragment

    def build_thing(self):
        """Builds a new Thing object from the serialized Thing Description."""

        return Thing(thing_fragment=self.to_thing_fragment())

    def get_forms(self, name):
        """Returns a list of FormDict for the interaction that matches the given name."""

        if name in self.properties:
            return self.get_property_forms(name)

        if name in self.actions:
            return self.get_action_forms(name)

        if name in self.events:
            return self.get_event_forms(name)

        return []

    def get_property_forms(self, name):
        """Returns a list of FormDict for the property that matches the given name."""

        return self.properties[name].forms

    def get_action_forms(self, name):
        """Returns a list of FormDict for the action that matches the given name."""

        return self.actions[name].forms

    def get_event_forms(self, name):
        """Returns a list of FormDict for the event that matches the given name."""

        return self.events[name].forms
