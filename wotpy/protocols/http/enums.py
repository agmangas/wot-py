#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to the HTTP server.
"""

from wotpy.utils.enums import EnumListMixin


class HTTPSchemes(EnumListMixin):
    """Enumeration of HTTP schemes."""

    HTTP = "http"
    HTTPS = "https"
