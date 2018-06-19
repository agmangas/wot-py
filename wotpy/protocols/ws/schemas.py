#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Schemas following the JSON Schema specification used to validate the shape of WebSockets messages.
"""

from wotpy.protocols.ws.enums import WebsocketMethods

JSON_RPC_VERSION = "2.0"

# Schema for message IDs

SCHEMA_ID = {
    "oneOf": [
        {"type": "string"},
        {"type": "integer"},
        {"type": "null"}
    ]
}

SCHEMA_REQUEST = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-request.json",
    "type": "object",
    "properties": {
        "jsonrpc": {
            "type": "string",
            "enum": [JSON_RPC_VERSION]
        },
        "method": {
            "type": "string",
            "enum": WebsocketMethods.list()
        },
        "params": {
            "oneOf": [
                {"type": "object"},
                {"type": "array"}
            ]
        },
        "id": SCHEMA_ID
    },
    "required": [
        "jsonrpc",
        "method"
    ]
}

SCHEMA_RESPONSE = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-response.json",
    "type": "object",
    "properties": {
        "jsonrpc": {
            "type": "string",
            "enum": ["2.0"]
        },
        "result": {},
        "id": SCHEMA_ID
    },
    "required": [
        "jsonrpc",
        "result",
        "id"
    ]
}

SCHEMA_ERROR = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-error.json",
    "type": "object",
    "properties": {
        "jsonrpc": {
            "type": "string",
            "enum": ["2.0"]
        },
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "integer"},
                "message": {"type": "string"},
                "data": {}
            },
            "required": [
                "code",
                "message"
            ]
        },
        "id": SCHEMA_ID
    },
    "required": [
        "jsonrpc",
        "error",
        "id"
    ]
}

SCHEMA_EMITTED_ITEM = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-emitted-item.json",
    "type": "object",
    "properties": {
        "subscription": {"type": "string"},
        "name": {"type": "string"},
        "data": {}
    },
    "required": [
        "subscription",
        "name",
        "data"
    ]
}

SCHEMA_PARAMS_READ_PROPERTY = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-read-property.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "required": [
        "name"
    ]
}

SCHEMA_PARAMS_WRITE_PROPERTY = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-write-property.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "value": {}
    },
    "required": [
        "name",
        "value"
    ]
}

SCHEMA_PARAMS_INVOKE_ACTION = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-invoke-action.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "parameters": {}
    },
    "required": [
        "name"
    ]
}

SCHEMA_PARAMS_ON_PROPERTY_CHANGE = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-on-property-change.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "required": [
        "name"
    ]
}

SCHEMA_PARAMS_ON_TD_CHANGE = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-on-td-change.json",
    "type": "object"
}

SCHEMA_PARAMS_ON_EVENT = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-on-event.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "required": [
        "name"
    ]
}

SCHEMA_PARAMS_DISPOSE = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-dispose.json",
    "type": "object",
    "properties": {
        "subscription": {"type": "string"}
    },
    "required": [
        "subscription"
    ]
}
