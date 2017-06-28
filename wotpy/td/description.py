#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from jsonschema import validate

from wotpy.td.interaction import Interaction, InteractionTypes

SCHEMA_THING_DESCRIPTION = {
    '$schema': 'http://json-schema.org/schema#',
    'id': 'http://fundacionctic.org/schemas/thing-description.json',
    'type': 'object',
    'properties': {
        '@context': {
            'oneOf': [
                {'type': 'string'},
                {
                    'type': 'array',
                    'items': {
                        'oneOf': [
                            {'type': 'string'},
                            {'type': 'object'}
                        ]
                    }
                }
            ]
        },
        'name': {'type': 'string'},
        'base': {'type': 'string'},
        '@type': {
            'type': 'array',
            'items': {'type': 'string'}
        },
        'interaction': {
            'type': 'array',
            'items': {
                'anyOf': [
                    Interaction.schema(InteractionTypes.PROPERTY),
                    Interaction.schema(InteractionTypes.ACTION),
                    Interaction.schema(InteractionTypes.EVENT)
                ]
            }
        }
    },
    'required': [
        'name'
    ]
}


class ThingDescription(object):
    """A ThingDescription JSON-LD document."""

    @classmethod
    def loads(cls, json_str):
        """Build a ThingDescription instance from
        a JSON document serialized as string."""

        return ThingDescription(json.loads(json_str))

    @classmethod
    def schema(cls):
        """Returns the JSON schema that describes a thing description."""

        return SCHEMA_THING_DESCRIPTION

    def __init__(self, doc):
        self._doc = doc

    def validate(self):
        """Validates this instance agains its JSON schema."""

        validate(self._doc, self.schema())

    @property
    def name(self):
        """Name getter."""

        return self._doc.get('name')

    @property
    def base(self):
        """Base getter."""

        return self._doc.get('base')

    @property
    def type(self):
        """Type getter."""

        return self._doc.get('@type')

    @property
    def context(self):
        """Context getter."""

        return self._doc.get('@context')

    @property
    def interaction(self):
        """Returns a list of Interaction instances that represent
        the interactions contained in this Thing Description."""

        return [Interaction(item) for item in self._doc.get('interaction', [])]
