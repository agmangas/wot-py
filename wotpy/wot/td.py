#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent the JSON and JSON-LD serialization formats of a Thing Description document.
"""

import copy
import json

import jsonschema
import six

from wotpy.wot.thing import Thing
from wotpy.wot.validation import SCHEMA_THING, InvalidDescription
from wotpy.wot.dictionaries.thing import ThingFragment


class ThingDescription(object):
    """Class that represents a Thing Description document.
    Contains logic to validate and transform a Thing to a serialized TD and vice versa."""

    def __init__(self, doc):
        """Constructor.
        Validates that the document conforms to the TD schema."""

        self._doc = json.loads(doc) if isinstance(doc, six.string_types) else doc
        self._thing_fragment = ThingFragment(self._doc)
        self._doc_clean = self._thing_fragment.to_dict()

        self.validate(doc=self._doc_clean)

    @classmethod
    def validate(cls, doc):
        """Validates the given Thing Description document against its schema.
        Raises ValidationError if validation fails."""

        try:
            jsonschema.validate(doc, SCHEMA_THING)
        except (jsonschema.ValidationError, TypeError) as ex:
            raise InvalidDescription(str(ex))

    @classmethod
    def from_thing(cls, thing):
        """Builds an instance of a JSON-serialized Thing Description from a Thing object."""

        def json_interaction(intrct):
            """Returns the JSON serialization of an Interaction instance."""

            ret = intrct.interaction_fragment.to_dict()

            ret.update({
                "forms": [form.form_dict.to_dict() for form in intrct.forms]
            })

            return ret

        doc = thing.thing_fragment.to_dict()

        doc.update({
            "properties": {
                key: json_interaction(val)
                for key, val in six.iteritems(thing.properties)
            }
        })

        doc.update({
            "actions": {
                key: json_interaction(val)
                for key, val in six.iteritems(thing.actions)
            }
        })

        doc.update({
            "events": {
                key: json_interaction(val)
                for key, val in six.iteritems(thing.events)
            }
        })

        return ThingDescription(doc)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal ThingFragment before propagating the exception."""

        return getattr(self._thing_fragment, name)

    def to_dict(self):
        """Returns the JSON Thing Description as a dict."""

        return copy.deepcopy(self._doc_clean)

    def to_str(self):
        """Returns the JSON Thing Description as a string."""

        return json.dumps(self._doc_clean)

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

        if name not in self.properties:
            raise ValueError("Missing property: {}".format(name))

        return self.properties[name].forms

    def get_action_forms(self, name):
        """Returns a list of FormDict for the action that matches the given name."""

        if name not in self.actions:
            raise ValueError("Missing action: {}".format(name))

        return self.actions[name].forms

    def get_event_forms(self, name):
        """Returns a list of FormDict for the event that matches the given name."""

        if name not in self.events:
            raise ValueError("Missing event: {}".format(name))

        return self.events[name].forms
