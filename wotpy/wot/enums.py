#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that contain various enumerations.
"""

from wotpy.utils.enums import EnumListMixin


class DiscoveryMethod(EnumListMixin):
    """Enumeration of discovery types."""

    ANY = "any"
    LOCAL = "local"
    NEARBY = "nearby"
    DIRECTORY = "directory"
    BROADCAST = "broadcast"
    OTHER = "other"


class TDChangeType(EnumListMixin):
    """Represents the change type, whether has it been
    applied on properties, Actions or Events."""

    PROPERTY = "property"
    ACTION = "action"
    EVENT = "event"


class TDChangeMethod(EnumListMixin):
    """This attribute tells what operation has been
    applied to the TD: addition, removal or change."""

    ADD = "add"
    REMOVE = "remove"
    CHANGE = "change"


class DefaultThingEvent(EnumListMixin):
    """Enumeration for the default events
    that are supported on all ExposedThings."""

    PROPERTY_CHANGE = "propertychange"
    ACTION_INVOCATION = "actioninvocation"
    DESCRIPTION_CHANGE = "descriptionchange"
