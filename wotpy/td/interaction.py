#!/usr/bin/env python
# -*- coding: utf-8 -*-

from jsonschema import validate

from wotpy.td.link import InteractionLink

SCHEMA_INTERACTION_BASE = {
    '$schema': 'http://json-schema.org/schema#',
    'id': 'http://fundacionctic.org/schemas/interaction-base.json',
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        '@type': {'type': 'array', 'items': {'type': 'string'}},
        'link': {'type': 'array', 'items': InteractionLink.schema()}
    },
    'required': [
        'name',
        '@type'
    ]
}

SCHEMA_INTERACTION_PROPERTY = {
    '$schema': 'http://json-schema.org/schema#',
    'id': 'http://fundacionctic.org/schemas/interaction-property.json',
    'allOf': [
        SCHEMA_INTERACTION_BASE,
        {
            'type': 'object',
            'properties': {
                'outputData': {'type': 'object'},
                'writable': {'type': 'boolean'},
                'stability': {'type': 'number'}
            },
            'required': [
                'writable'
            ]
        }
    ]
}

SCHEMA_INTERACTION_ACTION = {
    '$schema': 'http://json-schema.org/schema#',
    'id': 'http://fundacionctic.org/schemas/interaction-action.json',
    'allOf': [
        SCHEMA_INTERACTION_BASE,
        {
            'type': 'object',
            'properties': {
                'inputData': {'type': 'object'},
                'outputData': {'type': 'object'}
            }
        }
    ]
}

SCHEMA_INTERACTION_EVENT = {
    '$schema': 'http://json-schema.org/schema#',
    'id': 'http://fundacionctic.org/schemas/interaction-event.json',
    'allOf': [
        SCHEMA_INTERACTION_BASE,
        {
            'type': 'object',
            'properties': {
                'outputData': {'type': 'object'}
            }
        }
    ]
}


class InteractionTypes(object):
    """Enumeration of interaction types."""

    PROPERTY = 'Property'
    ACTION = 'Action'
    EVENT = 'Event'

    @classmethod
    def list(cls):
        """Returns a list with all interaction types."""

        return [cls.PROPERTY, cls.ACTION, cls.EVENT]


class Interaction(object):
    """An interaction sub-document contained within
    a Thing Description JSON-LD document."""

    @classmethod
    def schema(cls, interaction_type):
        """Returns the JSON schema that describes an
        interaction for the given interaction type."""

        type_schema_dict = {
            InteractionTypes.PROPERTY: SCHEMA_INTERACTION_PROPERTY,
            InteractionTypes.ACTION: SCHEMA_INTERACTION_ACTION,
            InteractionTypes.EVENT: SCHEMA_INTERACTION_EVENT
        }

        assert interaction_type in type_schema_dict

        return type_schema_dict[interaction_type]

    def __init__(self, doc):
        self._doc = doc

    def validate(self):
        """Validates this instance agains its JSON schema."""

        validate(self._doc, self.schema(self.interaction_type))

    @property
    def interaction_type(self):
        """Returns the interaction type."""

        for item in self.type:
            if item in InteractionTypes.list():
                return item

        raise ValueError('Unknown interaction type')

    @property
    def type(self):
        """Type getter."""

        return self._doc.get('@type')

    @property
    def name(self):
        """Name getter."""

        return self._doc.get('name')

    @property
    def output_data(self):
        """outputData getter."""

        return self._doc.get('outputData')

    @property
    def input_data(self):
        """inputData getter."""

        return self._doc.get('inputData')

    @property
    def writable(self):
        """Writable getter."""

        return self._doc.get('writable')

    @property
    def stability(self):
        """Stability getter."""

        return self._doc.get('stability')

    @property
    def link(self):
        """Returns a list of InteractionLink instances that
        represent the links contained in this interaction."""

        return [InteractionLink(item) for item in self._doc.get('link', [])]
