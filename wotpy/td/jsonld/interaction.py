#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the JSON-LD serialization of an Interaction document.
"""

from jsonschema import validate

from wotpy.td.enums import InteractionTypes
from wotpy.td.jsonld.form import JsonLDForm
from wotpy.td.jsonld.schemas import interaction_schema_for_type


class JsonLDInteraction(object):
    """Wrapper class for an Interaction document serialized in JSON-LD."""

    def __init__(self, doc, jsonld_td):
        self._doc = doc
        self.jsonld_td = jsonld_td
        self.validate()

    def validate(self):
        """Validates this instance agains its JSON schema."""

        validate(self._doc, interaction_schema_for_type(self.interaction_type))

    @property
    def doc(self):
        """Raw document dictionary property."""

        return self._doc

    @property
    def interaction_type(self):
        """Returns the interaction type."""

        for item in self.type:
            if item in InteractionTypes.list():
                return item

        raise ValueError("Unknown interaction type")

    @property
    def type(self):
        """Type property."""

        return self._doc.get("@type")

    @property
    def name(self):
        """Name property."""

        return self._doc.get("name")

    @property
    def output_data(self):
        """outputData property."""

        return self._doc.get("outputData")

    @property
    def input_data(self):
        """inputData property."""

        return self._doc.get("inputData")

    @property
    def writable(self):
        """Writable property."""

        return self._doc.get("writable")

    @property
    def observable(self):
        """Observable property."""

        return self._doc.get("observable")

    @property
    def form(self):
        """Returns a list of JsonLDForm instances that
        represent the forms contained in this interaction."""

        return [JsonLDForm(item, self) for item in self._doc.get("form", [])]

    @property
    def metadata(self):
        """Returns a dict containing the metadata for this interaction.
        This is, all fields that are not part of the expected set."""

        doc_schema = interaction_schema_for_type(self.interaction_type)

        base_keys = []

        for sub_schema in doc_schema["allOf"]:
            base_keys += list(sub_schema["properties"].keys())

        meta_keys = [key for key in list(self._doc.keys()) if key not in base_keys]

        return {key: self._doc[key] for key in meta_keys}
