#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.utils.enums import EnumListMixin


class DiscoveryMethod(EnumListMixin):
    """Enumeration of discovery types."""

    ANY = "any"
    LOCAL = "local"
    NEARBY = "nearby"
    DIRECTORY = "directory"
    BROADCAST = "broadcast"
    OTHER = "other"


class RequestType(EnumListMixin):
    """Enumeration of request types."""

    PROPERTY = "property"
    ACTION = "action"
    EVENT = "event"
    TD = "td"


class TDChangeType(EnumListMixin):
    """Represents the change type, whether has it been
    applied on properties, Actions or Events."""

    PROPERTY = "property"
    ACTION = "action"
    EVENT = "event"


class TDChangeMethod(EnumListMixin):
    """This attribute tells what operation has been
    applied, addition, removal or change.."""

    ADD = "add"
    REMOVE = "remove"
    CHANGE = "change"
