#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the JSON-LD serialization of a Thing Description document.
"""

import six
from jsonschema import validate, ValidationError

from wotpy.td.constants import WOT_TD_CONTEXT_URL
from wotpy.td.enums import InteractionTypes
from wotpy.td.interaction import Action, Event, Property
from wotpy.td.jsonld.schemas import SCHEMA_THING_DESCRIPTION
from wotpy.td.thing import Thing


class InvalidDescription(Exception):
    """Exception raised when a document for an object
    in the TD hierarchy has an invalid format."""

    pass


class ThingDescription(object):
    """Wrapper class for a Thing Description JSON-LD document."""

    def __init__(self, doc):
        """Constructor.
        Raises InvalidDescription if the given document does not conform to the TD schema."""

        self.validate(doc=doc)
        self._doc = doc

    @classmethod
    def validate(cls, doc):
        """Validates the given Thing Description document against its schema.
        Raises ValidationError if validation fails."""

        try:
            validate(doc, SCHEMA_THING_DESCRIPTION)
        except ValidationError as ex:
            raise InvalidDescription(str(ex))

        if WOT_TD_CONTEXT_URL not in (doc.get("@context", [])):
            raise InvalidDescription("Missing context: {}".format(WOT_TD_CONTEXT_URL))

    def build_thing(self):
        """Builds a new Thing object from the serialized JSON-LD Thing Description."""

        thing = Thing(name=self._doc.get("name"))

        for context_item in self._doc.get("@context", []):
            if isinstance(context_item, six.string_types):
                thing.semantic_context.add(context_url=context_item)
            elif isinstance(context_item, dict):
                for ctx_key, ctx_val in six.iteritems(context_item):
                    thing.semantic_context.add(context_url=ctx_val, prefix=ctx_key)

        for val_type in self._doc.get("@type", []):
            thing.semantic_types.add(val_type)

        def _build_property(doc_intrct):
            return Property(
                thing=thing,
                name=doc_intrct.get("name"),
                output_data=doc_intrct.get("outputData"),
                writable=doc_intrct.get("writable", True),
                observable=doc_intrct.get("observable", True))

        def _build_action(doc_intrct):
            return Action(
                thing=thing,
                name=doc_intrct.get("name"),
                output_data=doc_intrct.get("outputData"),
                input_data=doc_intrct.get("inputData"))

        def _build_event(doc_intrct):
            return Event(
                thing=thing,
                name=doc_intrct.get("name"),
                output_data=doc_intrct.get("outputData"))

        builder_map = {
            InteractionTypes.PROPERTY: _build_property,
            InteractionTypes.ACTION: _build_action,
            InteractionTypes.EVENT: _build_event
        }

        for item in self._doc.get("interaction", []):
            interaction_type = next(
                item for item in item.get("@type", [])
                if item in InteractionTypes.list())

            builder_func = builder_map[interaction_type]
            interaction = builder_func(item)

            for val_type in item.get("@type", []):
                interaction.semantic_types.add(val_type)

            thing.add_interaction(interaction)

        return thing
