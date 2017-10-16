#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jsonschema import validate, ValidationError

from wotpy.td.jsonld.interaction import JsonLDInteraction
from wotpy.td.jsonld.schemas import SCHEMA_THING_DESCRIPTION


class JsonLDThingDescription(object):
    """Wrapper class for a Thing Description JSON-LD document."""

    TD_CONTEXT_URL = "https://w3c.github.io/wot/w3c-wot-td-context.jsonld"

    def __init__(self, doc, validation=True):
        self._doc = doc

        if validation:
            self.validate()

    def _validate_context(self):
        """Raises a JSON schema validation error if this document lacks the required context."""

        valid_urls = {
            self.TD_CONTEXT_URL,
            self.TD_CONTEXT_URL.replace("http://", "https://"),
            self.TD_CONTEXT_URL.replace("https://", "http://")
        }

        try:
            next(item for item in valid_urls if item in self.context)
        except StopIteration:
            raise ValidationError("Missing context: {}".format(self.TD_CONTEXT_URL))

    def validate(self):
        """Validates this instance agains its JSON schema."""

        validate(self._doc, SCHEMA_THING_DESCRIPTION)
        self._validate_context()

    @property
    def doc(self):
        """Document getter."""

        return self._doc

    @property
    def name(self):
        """Name getter."""

        return self._doc.get("name")

    @property
    def base(self):
        """Base getter."""

        return self._doc.get("base")

    @property
    def type(self):
        """Type getter."""

        return self._doc.get("@type")

    @property
    def context(self):
        """Context getter."""

        return self._doc.get("@context")

    @property
    def interaction(self):
        """Returns a list of Interaction instances that represent
        the interactions contained in this Thing Description."""

        return [JsonLDInteraction(item) for item in self._doc.get("interaction", [])]
