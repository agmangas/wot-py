#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jsonschema import validate

from wotpy.td.jsonld.schemas import SCHEMA_INTERACTION_LINK


class JsonLDLink(object):
    """Wrapper class for a Link JSON-LD document."""

    def __init__(self, doc, validation=True):
        self._doc = doc

        if validation:
            self.validate()

    def validate(self):
        """Validates this instance agains its JSON schema."""

        validate(self._doc, SCHEMA_INTERACTION_LINK)

    @property
    def doc(self):
        """Raw document dictionary property."""

        return self._doc

    @property
    def href(self):
        """Href property."""

        return self._doc.get("href")

    @property
    def media_type(self):
        """Media type property."""

        return self._doc.get("mediaType")
