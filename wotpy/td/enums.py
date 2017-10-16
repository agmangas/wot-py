#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.utils.enums import EnumListMixin


class InteractionTypes(EnumListMixin):
    """Enumeration of interaction types."""

    PROPERTY = "Property"
    ACTION = "Action"
    EVENT = "Event"
