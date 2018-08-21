#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to the CoAP server.
"""

from wotpy.utils.enums import EnumListMixin


class CoAPSchemes(EnumListMixin):
    """Enumeration of CoAP schemes."""

    COAP = "coap"
    COAPS = "coaps"
