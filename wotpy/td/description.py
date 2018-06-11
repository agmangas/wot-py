#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent the JSON and JSON-LD serialization formats of a Thing Description document.
"""

import copy
import json

import jsonschema
import six
from six.moves import urllib

from wotpy.td.constants import WOT_TD_CONTEXT_URL, WOT_COMMON_CONTEXT_URL
from wotpy.td.interaction import Property, Action, Event
from wotpy.td.thing import Thing
from wotpy.td.validation import SCHEMA_THING, InvalidDescription


class ThingDescription(object):
    """Class that represents a Thing Description document.
    Contains logic to validate and transform a Thing to a serialized TD and vice versa."""

    def __init__(self, doc):
        """Constructor.
        Validates that the document conforms to the TD schema."""

        self._doc = json.loads(doc) if isinstance(doc, six.string_types) else doc
        self.validate(doc=self._doc)

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

        def filter_dict(the_dict):
            """Filters all the None values in the given dict."""

            return {key: the_dict[key] for key in the_dict if the_dict[key] is not None}

        def json_form(form):
            """Returns the JSON serialization of a Form instance."""

            ret = {
                "href": form.href,
                "mediaType": form.media_type,
                "rel": form.rel,
                "security": form.security
            }

            return filter_dict(ret)

        def json_property(prop):
            """Returns the JSON serialization of a Property instance."""

            ret = {
                "label": prop.label,
                "description": prop.description,
                "observable": prop.observable,
                "writable": prop.writable,
                "type": prop.type,
                "forms": [json_form(form) for form in prop.forms]
            }

            return filter_dict(ret)

        def json_action(action):
            """Returns the JSON serialization of an Action instance."""

            ret = {
                "label": action.label,
                "description": action.description,
                "input": action.input,
                "output": action.output,
                "forms": [json_form(form) for form in action.forms]
            }

            return filter_dict(ret)

        def json_event(event):
            """Returns the JSON serialization of an Event instance."""

            ret = {
                "label": event.label,
                "description": event.description,
                "type": event.type,
                "forms": [json_form(form) for form in event.forms]
            }

            return filter_dict(ret)

        doc = {
            "@context": [
                WOT_TD_CONTEXT_URL,
                WOT_COMMON_CONTEXT_URL
            ],
            "id": thing.id,
            "label": thing.label,
            "description": thing.description,
            "support": thing.support,
            "properties": {
                key: json_property(val)
                for key, val in six.iteritems(thing.properties)
            },
            "actions": {
                key: json_action(val)
                for key, val in six.iteritems(thing.actions)
            },
            "events": {
                key: json_event(val)
                for key, val in six.iteritems(thing.events)
            }
        }

        doc = filter_dict(doc)

        return ThingDescription(doc)

    @property
    def doc(self):
        """Thing Description document as a dict."""

        return self._doc

    @property
    def id(self):
        """Thing ID."""

        return self._doc.get("id")

    @property
    def name(self):
        """Name (ID) of the Thing."""

        return self.id

    @property
    def base(self):
        """Base URI that is valid for all defined local interaction resources."""

        return self._doc.get("base")

    @property
    def properties(self):
        """Property interactions."""

        return self._doc.get("properties", {})

    @property
    def actions(self):
        """Action interactions."""

        return self._doc.get("actions", {})

    @property
    def events(self):
        """Event interactions."""

        return self._doc.get("events", {})

    def to_dict(self):
        """Returns the JSON Thing Description as a dict."""

        return copy.deepcopy(self.doc)

    def to_str(self):
        """Returns the JSON Thing Description as a string."""

        return json.dumps(self._doc)

    def build_thing(self):
        """Builds a new Thing object from the serialized Thing Description.
        Ignores the Form objects defined on all interactions,
        as the Forms can only be defined by their respective servers."""

        thing = Thing(**self._doc)

        for name, fields in six.iteritems(self._doc.get("properties", {})):
            proprty = Property(thing=thing, id=name, **fields)
            thing.add_interaction(proprty)

        for name, fields in six.iteritems(self._doc.get("actions", {})):
            action = Action(thing=thing, id=name, **fields)
            thing.add_interaction(action)

        for name, fields in six.iteritems(self._doc.get("events", {})):
            event = Event(thing=thing, id=name, **fields)
            thing.add_interaction(event)

        return thing

    def resolve_form_uri(self, form):
        """Resolves the given Form URI.
        When the Form href does not contain a full URL the base URI is joined with said href."""

        href = form.get("href")
        href_parsed = urllib.parse.urlparse(href)

        if self.base and not href_parsed.scheme:
            return urllib.parse.urljoin(self.base, href)

        if href_parsed.scheme:
            return href

        return None

    def get_forms(self, name):
        """Returns the Form objects for the interaction with the given name."""

        if name in self.properties:
            return self.get_property_forms(name)

        if name in self.actions:
            return self.get_action_forms(name)

        if name in self.events:
            return self.get_event_forms(name)

        return []

    def get_property_forms(self, name):
        """Returns the Form objects for the given Property."""

        return self._doc.get("properties", {}).get(name, {}).get("forms", [])

    def get_action_forms(self, name):
        """Returns the Form objects for the given Action."""

        return self._doc.get("actions", {}).get(name, {}).get("forms", [])

    def get_event_forms(self, name):
        """Returns the Form objects for the given Event."""

        return self._doc.get("events", {}).get(name, {}).get("forms", [])
