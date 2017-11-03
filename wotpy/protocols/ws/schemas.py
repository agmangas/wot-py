#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.protocols.ws.enums import WebsocketMethods

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

# Schema for the parameters of a "get property" invocation

SCHEMA_PARAMS_GET_PROPERTY = {
    "type": "object",
    "properties": {"name": {"type": "string"}},
    "required": ["name"]
}

# Schema for the parameters of a "set property" invocation

SCHEMA_PARAMS_SET_PROPERTY = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "value": {"type": "string"}
    },
    "required": ["name", "value"]
}
