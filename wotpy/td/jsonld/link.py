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

    @property
    def meta(self):
        """Returns a dict containing the metadata for this link.
        This is, all fields that are not part of the expected set."""

        base_keys = list(SCHEMA_INTERACTION_LINK["properties"].keys())
        meta_keys = [key for key in list(self._doc.keys()) if key not in base_keys]

        return {key: self._doc[key] for key in meta_keys}
