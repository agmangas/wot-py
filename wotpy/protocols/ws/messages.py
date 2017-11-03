#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from jsonschema import validate

from wotpy.protocols.ws.enums import WebsocketErrors
from wotpy.protocols.ws.schemas import SCHEMA_REQUEST, SCHEMA_RESPONSE, JSON_RPC_VERSION


class WebsocketMessageException(Exception):
    """Exception raised when a WS message appears to be invalid."""

    pass


class WebsocketMessageRequest(object):
    """Represents a message received on a websocket that
    contains a JSON-RPC WoT action request."""

    @classmethod
    def from_raw(cls, raw_msg):
        """Builds a new WebsocketMessageRequest instance from a raw socket message.
        Raises WebsocketMessageException if the message is invalid."""

        try:
            request_msg = json.loads(raw_msg)
            validate(request_msg, SCHEMA_REQUEST)

            return WebsocketMessageRequest(
                method=request_msg["method"],
                params=request_msg["params"],
                req_id=request_msg.get("id", None))
        except Exception as ex:
            raise WebsocketMessageException(ex.message)

    def __init__(self, method, params, req_id=None):
        self.method = method
        self.params = params
        self.req_id = req_id

        validate(self.to_dict(), SCHEMA_REQUEST)

    def to_dict(self):
        """Returns this message as a dict."""

        request_msg = {
            "jsonrpc": JSON_RPC_VERSION,
            "method": self.method,
            "params": self.params,
            "id": self.req_id
        }

        return request_msg

    def to_json(self):
        """Returns this message as a JSON string."""

        return json.dumps(self.to_dict())


class WebsocketMessageResponse(object):
    """Represents a WoT Websockets JSON-RPC response message."""

    @classmethod
    def from_raw(cls, raw_msg):
        """Builds a new WebsocketMessageResponse instance from a raw socket message.
        Raises WebsocketMessageException if the message is invalid."""

        try:
            response_msg = json.loads(raw_msg)
            validate(response_msg, SCHEMA_RESPONSE)

            assert "result" in response_msg
            assert "error" not in response_msg

            return WebsocketMessageResponse(
                result=response_msg["result"],
                res_id=response_msg.get("id", None))
        except Exception as ex:
            raise WebsocketMessageException(ex.message)

    def __init__(self, result, res_id=None):
        self.result = result
        self.res_id = res_id

        validate(self.to_dict(), SCHEMA_RESPONSE)

    def to_dict(self):
        """Returns this message as a dict."""

        error_msg = {
            "jsonrpc": JSON_RPC_VERSION,
            "result": self.result,
            "id": self.res_id
        }

        return error_msg

    def to_json(self):
        """Returns this message as a JSON string."""

        return json.dumps(self.to_dict())


class WebsocketMessageError(object):
    """Represents a WoT Websockets JSON-RPC error message."""

    @classmethod
    def from_raw(cls, raw_msg):
        """Builds a new WebsocketMessageError instance from a raw socket message.
        Raises WebsocketMessageException if the message is invalid."""

        try:
            error_msg = json.loads(raw_msg)
            validate(error_msg, SCHEMA_RESPONSE)

            assert "error" in error_msg
            assert "result" not in error_msg

            return WebsocketMessageError(
                message=error_msg["error"]["message"],
                code=error_msg["error"]["code"],
                res_id=error_msg.get("id", None))
        except Exception as ex:
            raise WebsocketMessageException(ex.message)

    def __init__(self, message, code=WebsocketErrors.INTERNAL_ERROR, res_id=None):
        self.message = message
        self.res_id = res_id
        self.code = code

        validate(self.to_dict(), SCHEMA_RESPONSE)

    def to_dict(self):
        """Returns this message as a dict."""

        error_msg = {
            "jsonrpc": JSON_RPC_VERSION,
            "error": {
                "code": self.code,
                "message": self.message
            },
            "id": self.res_id
        }

        return error_msg

    def to_json(self):
        """Returns this message as a JSON string."""

        return json.dumps(self.to_dict())
