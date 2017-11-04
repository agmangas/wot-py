#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.utils.enums import EnumListMixin


class WebsocketMethods(EnumListMixin):
    """Enumeration of available websocket message actions."""

    GET_PROPERTY = "get_property"
    SET_PROPERTY = "set_property"
    INVOKE_ACTION = "invoke_action"
    OBSERVE = "observe"
    DISPOSE = "dispose"


class WebsocketErrors(EnumListMixin):
    """Enumeration of JSON RPC error codes."""

    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_METHOD_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SUBSCRIPTION_ERROR = -32000
