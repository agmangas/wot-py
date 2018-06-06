#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to the various protocol servers.
"""

from wotpy.utils.enums import EnumListMixin


class Protocols(EnumListMixin):
    """Enumeration of protocol types."""

    HTTP = "HTTP"
    WEBSOCKETS = "WEBSOCKETS"


class ProtocolSchemes(EnumListMixin):
    """Enumeration of protocol schemes."""

    HTTP = "http"
    WS = "ws"
    WSS = "wss"
