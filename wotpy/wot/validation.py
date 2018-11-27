#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Schemas following the JSON Schema specification used to validate the shape of Thing Description documents.
"""

import re

from wotpy.wot.enums import InteractionTypes

REGEX_SAFE_NAME = r"^[a-zA-Z0-9_-]+$"
REGEX_ANY_URI = r"^((\w+:(\/?\/?)[^\s]+)|((..\/)+)[^\s]*)$"

DATA_TYPES_ENUM = [
    "array",
    "boolean",
    "number",
    "integer",
    "object",
    "string",
    "null"
]

SCHEMA_DATA_SCHEMA = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/data-schema.json",
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "title": {"type": "string"},
        "type": {
            "type": "string",
            "enum": DATA_TYPES_ENUM
        },
        "const": {},
        "unit": {"type": "string"},
        "enum": {
            "type": "array",
            "items": {}
        },
        "readOnly": {"type": "boolean"},
        "writeOnly": {"type": "boolean"}
    },
    "required": [
        "type"
    ]
}

SCHEMA_SECURITY_SCHEME = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/security-scheme.json",
    "type": "object",
    "properties": {
        "scheme": {"type": "string"},
        "description": {"type": "string"},
        "proxyUrl": {"type": "string"}
    },
    "required": [
        "scheme"
    ]
}

SCHEMA_LINK = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/link.json",
    "type": "object",
    "properties": {
        "href": {
            "type": "string",
            "pattern": REGEX_ANY_URI
        },
        "type": {"type": "string"},
        "rel": {"type": "string"},
        "anchor": {
            "type": "string",
            "pattern": REGEX_ANY_URI
        },
    },
    "required": [
        "href"
    ]
}

SCHEMA_FORM = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/form.json",
    "type": "object",
    "properties": {
        "href": {"type": "string"},
        "contentType": {
            "type": "string",
            "default": "application/json"
        },
        "op": {"type": "string"},
        "subprotocol": {"type": "string"},
        "security": {
            "type": "array",
            "items": SCHEMA_SECURITY_SCHEME
        },
        "scopes": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": [
        "href"
    ]
}

SCHEMA_INTERACTION_PATTERN = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/interaction-pattern.json",
    "type": "object",
    "properties": {
        "forms": {
            "type": "array",
            "items": SCHEMA_FORM
        },
        "title": {"type": "string"},
        "uriVariables": {
            "type": "object",
            "patternProperties": {REGEX_SAFE_NAME: SCHEMA_DATA_SCHEMA},
            "additionalProperties": False
        },
        "description": {"type": "string"},
        "security": {
            "type": "array",
            "items": SCHEMA_SECURITY_SCHEME
        },
        "scopes": {
            "type": "array",
            "items": {"type": "string"}
        }
    }
}

SCHEMA_PROPERTY = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/property.json",
    "allOf": [
        SCHEMA_INTERACTION_PATTERN,
        SCHEMA_DATA_SCHEMA,
        {
            "type": "object",
            "properties": {
                "observable": {
                    "type": "boolean",
                    "default": False
                }
            }
        }
    ]
}

SCHEMA_EVENT = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/event.json",
    "allOf": [
        SCHEMA_INTERACTION_PATTERN,
        {
            "type": "object",
            "properties": {
                "subscription": SCHEMA_DATA_SCHEMA,
                "data": SCHEMA_DATA_SCHEMA,
                "cancellation": SCHEMA_DATA_SCHEMA
            }
        }
    ]
}

SCHEMA_ACTION = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/action.json",
    "allOf": [
        SCHEMA_INTERACTION_PATTERN,
        {
            "type": "object",
            "properties": {
                "input": SCHEMA_DATA_SCHEMA,
                "output": SCHEMA_DATA_SCHEMA,
                "safe": {
                    "type": "boolean",
                    "default": False
                },
                "idempotent": {
                    "type": "boolean",
                    "default": False
                }
            }
        }
    ]
}

SCHEMA_VERSIONING = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/versioning.json",
    "type": "object",
    "properties": {
        "instance": {"type": "string"}
    },
    "required": [
        "instance"
    ]
}

SCHEMA_THING = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/thing.json",
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "pattern": REGEX_ANY_URI
        },
        "version": SCHEMA_VERSIONING,
        "name": {"type": "string"},
        "description": {"type": "string"},
        "support": {"type": "string"},
        "created": {"type": "string"},
        "lastModified": {"type": "string"},
        "base": {
            "type": "string",
            "pattern": REGEX_ANY_URI
        },
        "properties": {
            "type": "object",
            "patternProperties": {REGEX_SAFE_NAME: SCHEMA_PROPERTY},
            "additionalProperties": False
        },
        "actions": {
            "type": "object",
            "patternProperties": {REGEX_SAFE_NAME: SCHEMA_ACTION},
            "additionalProperties": False
        },
        "events": {
            "type": "object",
            "patternProperties": {REGEX_SAFE_NAME: SCHEMA_EVENT},
            "additionalProperties": False
        },
        "links": {
            "type": "array",
            "items": SCHEMA_LINK
        },
        "security": {
            "type": "array",
            "items": SCHEMA_SECURITY_SCHEME
        }
    },
    "required": [
        "id",
        "name",
        "security"
    ]
}


def interaction_schema_for_type(interaction_type):
    """Returns the JSON schema that describes an
    interaction for the given interaction type."""

    type_schema_dict = {
        InteractionTypes.PROPERTY: SCHEMA_PROPERTY,
        InteractionTypes.ACTION: SCHEMA_ACTION,
        InteractionTypes.EVENT: SCHEMA_EVENT
    }

    assert interaction_type in type_schema_dict

    return type_schema_dict[interaction_type]


def is_valid_uri(val):
    """Returns True if the given value is a valid URI."""

    return False if re.match(REGEX_ANY_URI, val) is None else True


def is_valid_safe_name(val):
    """Returns True if the given value is a safe machine-readable name."""

    return False if re.match(REGEX_SAFE_NAME, val) is None else True


class InvalidDescription(Exception):
    """Exception raised when a document for an object
    in the TD hierarchy has an invalid format."""

    pass
