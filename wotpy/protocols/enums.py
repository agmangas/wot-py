#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.utils.enums import EnumListMixin


class ProtocolTypes(EnumListMixin):
    """Enumeration of protocol types."""

    HTTP = "HTTP"
    WS = "WS"
