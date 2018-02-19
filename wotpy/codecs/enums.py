#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to codecs.
"""

from wotpy.utils.enums import EnumListMixin


class MediaTypes(EnumListMixin):
    """Enumeration of media types."""

    JSON = "application/json"
    TEXT = "text/plain"
