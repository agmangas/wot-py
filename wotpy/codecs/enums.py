#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.utils.enums import EnumListMixin


class MediaTypes(EnumListMixin):
    """Enumeration of media types."""

    JSON = "application/json"
    TEXT = "text/plain"
