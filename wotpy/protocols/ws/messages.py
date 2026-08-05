#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Classes that represent JSON-RPC messages exchanged over WebSockets.
"""

import json

from jsonschema import validate, ValidationError

from wotpy.protocols.ws.enums import WebsocketErrors
from wotpy.protocols.ws.schemas import \
    SCHEMA_REQUEST, \
    SCHEMA_RESPONSE, \
    SCHEMA_EMITTED_ITEM, \
    SCHEMA_ERROR, \
    JSON_RPC_VERSION
from wotpy.utils.utils import to_json_obj


def parse_ws_message(raw_msg):
    """Takes a raw WebSockets message and attempts
    to parse it to create a message instance."""

    msg_klasses = [
        WebsocketMessageRequest,
        WebsocketMessageError,
        WebsocketMessageResponse,
        WebsocketMessageEmittedItem
    ]

    for klass in msg_klasses:
        try:
            msg_instance = klass.from_raw(raw_msg)
            return msg_instance
        except WebsocketMessageException:
            pass

    raise WebsocketMessageException("Invalid message: {}".format(raw_msg))


class WebsocketMessageException(Exception):
    """Exception raised when a WS message appears to be invalid."""

    pass


class WebsocketMessageRequest:
    """Represents a message received on a websocket that
    contains a JSON-RPC WoT action request."""

    @classmethod
    def from_raw(cls, raw_msg):
        """Builds a new WebsocketMessageRequest instance from a raw socket message.
        Raises WebsocketMessageException if the message is invalid."""

        try:
            msg = json.loads(raw_msg)
            validate(msg, SCHEMA_REQUEST)

            return WebsocketMessageRequest(
                method=msg["method"],
                params=msg["params"],
                msg_id=msg.get("id", None))
        except Exception as ex:
            raise WebsocketMessageException(str(ex))

    def __init__(self, method, params, msg_id=None):
        self.method = method
        self.params = params
        self.msg_id = msg_id

        try:
            validate(self.to_dict(), SCHEMA_REQUEST)
        except ValidationError as ex:
            raise WebsocketMessageError(str(ex))

    @property
    def id(self):
        """ID property."""

        return self.msg_id

    def to_dict(self):
        """Returns this message as a dict."""

        msg = {
            "jsonrpc": JSON_RPC_VERSION,
            "method": self.method,
            "params": self.params,
            "id": self.id
        }

        return msg

    def to_json(self):
        """Returns this message as a JSON string."""

        return json.dumps(self.to_dict())


class WebsocketMessageResponse:
    """Represents a WoT Websockets JSON-RPC response message."""

    @classmethod
    def from_raw(cls, raw_msg):
        """Builds a new WebsocketMessageResponse instance from a raw socket message.
        Raises WebsocketMessageException if the message is invalid."""

        try:
            msg = json.loads(raw_msg)
            validate(msg, SCHEMA_RESPONSE)

            return WebsocketMessageResponse(
                result=msg["result"],
                msg_id=msg.get("id", None))
        except Exception as ex:
            raise WebsocketMessageException(str(ex))

    def __init__(self, result, msg_id=None):
        self.result = result
        self.msg_id = msg_id

        try:
            validate(self.to_dict(), SCHEMA_RESPONSE)
        except ValidationError as ex:
            raise WebsocketMessageError(str(ex))

    @property
    def id(self):
        """ID property."""

        return self.msg_id

    def to_dict(self):
        """Returns this message as a dict."""

        msg = {
            "jsonrpc": JSON_RPC_VERSION,
            "result": self.result,
            "id": self.id
        }

        return msg

    def to_json(self):
        """Returns this message as a JSON string."""

        return json.dumps(self.to_dict())


class WebsocketMessageError:
    """Represents a WoT Websockets JSON-RPC error message."""

    @classmethod
    def from_raw(cls, raw_msg):
        """Builds a new WebsocketMessageError instance from a raw socket message.
        Raises WebsocketMessageException if the message is invalid."""

        try:
            msg = json.loads(raw_msg)
            validate(msg, SCHEMA_ERROR)

            return WebsocketMessageError(
                message=msg["error"]["message"],
                code=msg["error"]["code"],
                data=msg["error"].get("data", None),
                msg_id=msg.get("id", None))
        except Exception as ex:
            raise WebsocketMessageException(str(ex))

    def __init__(self, message, code=WebsocketErrors.INTERNAL_ERROR, data=None, msg_id=None):
        self.message = message
        self.msg_id = msg_id
        self.code = code
        self.data = data

        try:
            validate(self.to_dict(), SCHEMA_ERROR)
        except ValidationError as ex:
            raise WebsocketMessageError(str(ex))

    @property
    def id(self):
        """ID property."""

        return self.msg_id

    def to_dict(self):
        """Returns this message as a dict."""

        msg = {
            "jsonrpc": JSON_RPC_VERSION,
            "error": {
                "code": self.code,
                "message": self.message,
                "data": self.data
            },
            "id": self.id
        }

        return msg

    def to_json(self):
        """Returns this message as a JSON string."""

        return json.dumps(self.to_dict())


class WebsocketMessageEmittedItem:
    """Represents a Websockets message for an item emitted by an active subscription."""

    @classmethod
    def from_raw(cls, raw_msg):
        """Builds a new WebsocketMessageEmittedItem instance from a raw socket message.
        Raises WebsocketMessageException if the message is invalid."""

        try:
            msg = json.loads(raw_msg)
            validate(msg, SCHEMA_EMITTED_ITEM)

            return WebsocketMessageEmittedItem(
                subscription_id=msg["subscription"],
                name=msg["name"],
                data=msg["data"])
        except Exception as ex:
            raise WebsocketMessageException(str(ex))

    def __init__(self, subscription_id, name, data):
        self.subscription_id = subscription_id
        self.name = name
        self.data = to_json_obj(data)

        try:
            validate(self.to_dict(), SCHEMA_EMITTED_ITEM)
        except ValidationError as ex:
            raise WebsocketMessageError(str(ex))

    def to_dict(self):
        """Returns this message as a dict."""

        msg = {
            "subscription": self.subscription_id,
            "name": self.name,
            "data": self.data
        }

        return msg

    def to_json(self):
        """Returns this message as a JSON string."""

        return json.dumps(self.to_dict())
