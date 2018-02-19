#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from jsonschema import validate, ValidationError

from wotpy.td.constants import WOT_TD_CONTEXT_URL
from wotpy.td.jsonld.interaction import JsonLDInteraction
from wotpy.td.jsonld.schemas import SCHEMA_THING_DESCRIPTION


class JsonLDThingDescription(object):
    """Wrapper class for a Thing Description JSON-LD document."""

    def __init__(self, doc):
        self._doc = doc
        self.validate()

    def validate(self):
        """Validates this instance agains its JSON schema."""

        validate(self._doc, SCHEMA_THING_DESCRIPTION)

        if WOT_TD_CONTEXT_URL not in (self.context or []):
            raise ValidationError("Missing context: {}".format(WOT_TD_CONTEXT_URL))

    @property
    def doc(self):
        """Raw document dictionary property."""

        return self._doc

    @property
    def name(self):
        """Name property."""

        return self._doc.get("name")

    @property
    def base(self):
        """Base property."""

        return self._doc.get("base")

    @property
    def type(self):
        """Type property."""

        return self._doc.get("@type")

    @property
    def context(self):
        """Context property."""

        return self._doc.get("@context")

    @property
    def interaction(self):
        """Returns a list of JsonLDInteraction instances that represent
        the interactions contained in this Thing Description."""

        return [JsonLDInteraction(item, self) for item in self._doc.get("interaction", [])]

    @property
    def security(self):
        """Security property."""

        return self._doc.get("security")

    @property
    def metadata(self):
        """Returns a dict containing the metadata for this thing description.
        This is, all fields that are not part of the expected set."""

        base_keys = list(SCHEMA_THING_DESCRIPTION["properties"].keys())
        meta_keys = [key for key in list(self._doc.keys()) if key not in base_keys]

        return {key: self._doc[key] for key in meta_keys}

    def to_json_str(self):
        """Returns the string serialization of this JSON-LD thing description."""

        return json.dumps(self.doc)
