#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jsonschema import validate

SCHEMA_INTERACTION_LINK = {
    '$schema': 'http://json-schema.org/schema#',
    'id': 'http://fundacionctic.org/schemas/interaction-link.json',
    'type': 'object',
    'properties': {
        'href': {'type': 'string'},
        'mediaType': {'type': 'string'}
    },
    'required': [
        'href',
        'mediaType'
    ]
}


class InteractionLink(object):
    """A link JSON-LD document."""

    @classmethod
    def schema(cls):
        """Returns the JSON schema that describes an interaction link."""

        return SCHEMA_INTERACTION_LINK

    def __init__(self, doc):
        self._doc = doc

    def validate(self):
        """Validates this instance agains its JSON schema."""

        validate(self._doc, self.schema())

    @property
    def href(self):
        """Href getter."""

        return self._doc.get('href')

    @property
    def media_type(self):
        """Media type getter."""

        return self._doc.get('mediaType')
