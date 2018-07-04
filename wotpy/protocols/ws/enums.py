#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
