#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 CTIC Centro Tecnologico
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
Enumeration classes related to the WebSockets server.
"""

from wotpy.utils.enums import EnumListMixin


class WebsocketMethods(EnumListMixin):
    """Enumeration of available websocket message actions."""

    READ_PROPERTY = "read_property"
    WRITE_PROPERTY = "write_property"
    INVOKE_ACTION = "invoke_action"
    ON_PROPERTY_CHANGE = "on_property_change"
    ON_TD_CHANGE = "on_td_change"
    ON_EVENT = "on_event"
    DISPOSE = "dispose"


class WebsocketErrors(EnumListMixin):
    """Enumeration of JSON RPC error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_METHOD_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SUBSCRIPTION_ERROR = -32000


class WebsocketSchemes(EnumListMixin):
    """Enumeration of Websocket schemes."""

    WS = "ws"
    WSS = "wss"
