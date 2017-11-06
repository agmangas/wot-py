#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.td.enums import InteractionTypes


def interaction_schema_for_type(interaction_type):
    """Returns the JSON schema that describes an
    interaction for the given interaction type."""

    type_schema_dict = {
        InteractionTypes.PROPERTY: SCHEMA_INTERACTION_PROPERTY,
        InteractionTypes.ACTION: SCHEMA_INTERACTION_ACTION,
        InteractionTypes.EVENT: SCHEMA_INTERACTION_EVENT
    }

    assert interaction_type in type_schema_dict

    return type_schema_dict[interaction_type]


SCHEMA_INTERACTION_LINK = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/interaction-link.json",
    "type": "object"
}

SCHEMA_INTERACTION_BASE = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/interaction-base.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "@type": {"type": "array", "items": {"type": "string"}},
        "link": {"type": "array", "items": SCHEMA_INTERACTION_LINK}
    },
    "required": [
        "name",
        "@type"
    ]
}

SCHEMA_INTERACTION_PROPERTY = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/interaction-property.json",
    "allOf": [
        SCHEMA_INTERACTION_BASE,
        {
            "type": "object",
            "properties": {
                "outputData": {"type": "object"},
                "writable": {"type": "boolean"}
            },
            "required": [
                "outputData"
            ]
        }
    ]
}

SCHEMA_INTERACTION_ACTION = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/interaction-action.json",
    "allOf": [
        SCHEMA_INTERACTION_BASE,
        {
            "type": "object",
            "properties": {
                "inputData": {"type": "object"},
                "outputData": {"type": "object"}
            }
        }
    ]
}

SCHEMA_INTERACTION_EVENT = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/interaction-event.json",
    "allOf": [
        SCHEMA_INTERACTION_BASE,
        {
            "type": "object",
            "properties": {
                "outputData": {"type": "object"}
            },
            "required": [
                "outputData"
            ]
        }
    ]
}

SCHEMA_THING_DESCRIPTION = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/thing-description.json",
    "type": "object",
    "properties": {
        "@context": {
            "type": "array",
            "items": {
                "oneOf": [
                    {"type": "string"},
                    {"type": "object"}
                ]
            }
        },
        "name": {"type": "string"},
        "base": {"type": "string"},
        "@type": {
            "type": "array",
            "items": {"type": "string"}
        },
        "interaction": {
            "type": "array",
            "items": {
                "anyOf": [
                    interaction_schema_for_type(InteractionTypes.PROPERTY),
                    interaction_schema_for_type(InteractionTypes.ACTION),
                    interaction_schema_for_type(InteractionTypes.EVENT)
                ]
            }
        },
        "security": {"type": "object"}
    },
    "required": [
        "name",
        "@context"
    ]
}
