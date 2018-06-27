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
    DIRECTORY = "directory"
    MULTICAST = "multicast"


class JSONType(EnumListMixin):
    """Enumeration of the types that values can take"""

    BOOLEAN = "boolean"
    NUMBER = "number"
    STRING = "string"
    OBJECT = "object"
    ARRAY = "array"


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


class DataType(EnumListMixin):
    """Defines the types that values can take."""

    BOOLEAN = "boolean"
    INTEGER = "integer"
    NUMBER = "number"
    STRING = "string"
    OBJECT = "object"
    ARRAY = "array"
    NULL = "null"


class SecuritySchemeType(EnumListMixin):
    """Defines the supported security schemes."""

    BASIC = "basic"
    DIGEST = "digest"
    BEARER = "bearer"
    POP = "pop"
    OAUTH2 = "oauth2"
    APIKEY = "apikey"


class AuthenticationType(EnumListMixin):
    """Defines the location of the authentication information."""

    HEADER = "header"
    BODY = "body"
    QUERY = "query"
    COOKIE = "cookie"
