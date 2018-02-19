#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumerations related to objects in the Thing hierarchy.
"""

from wotpy.utils.enums import EnumListMixin


class InteractionTypes(EnumListMixin):
    """Enumeration of interaction types."""

    PROPERTY = "Property"
    ACTION = "Action"
    EVENT = "Event"
