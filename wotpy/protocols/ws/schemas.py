#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.protocols.ws.enums import WebsocketMethods
from wotpy.wot.enums import RequestType

JSON_RPC_VERSION = "2.0"

# JSON schema for WS WoT request messages

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
        "id": {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"},
                {"type": "null"}
            ]
        }
    },
    "required": [
        "jsonrpc",
        "method"
    ]
}

# JSON schema for WS WoT response messages

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
        "id": {
            "oneOf": [
                {"type": "string"},
                {"type": "integer"},
                {"type": "null"}
            ]
        }
    },
    "required": [
        "jsonrpc",
        "id"
    ]
}

# JSON schema for WS WoT emitted items messages

SCHEMA_EMITTED_ITEM = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-emitted-item.json",
    "type": "object",
    "properties": {
        "subscription": {"type": "string"},
        "name": {"type": "string"},
        "data": {"type": "object"}
    },
    "required": [
        "subscription",
        "name",
        "data"
    ]
}

# Schema for the parameters of a "get property" invocation

SCHEMA_PARAMS_GET_PROPERTY = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-get-property.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "required": [
        "name"
    ]
}

# Schema for the parameters of a "set property" invocation

SCHEMA_PARAMS_SET_PROPERTY = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-set-property.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "value": {"type": "string"}
    },
    "required": [
        "name",
        "value"
    ]
}

# Schema for the parameters of an "observe" invocation

SCHEMA_PARAMS_OBSERVE = {
    "$schema": "http://json-schema.org/schema#",
    "id": "http://fundacionctic.org/schemas/wotpy-ws-params-observe.json",
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "request_type": {
            "type": "string",
            "enum": RequestType.list()
        }
    },
    "required": [
        "name",
        "request_type"
    ]
}
