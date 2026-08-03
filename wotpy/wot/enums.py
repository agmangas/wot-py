#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Classes that contain various enumerations.
"""

from wotpy.utils.enums import EnumListMixin


class DiscoveryMethod(EnumListMixin):
    """Enumeration of discovery types."""

    ANY = "any"
    LOCAL = "local"
    DIRECTORY = "directory"


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

    NOSEC = "nosec"
    AUTO = "auto"
    COMBO = "combo"
    BASIC = "basic"
    DIGEST = "digest"
    APIKEY = "apikey"
    BEARER = "bearer"
    PSK = "psk"
    OAUTH2 = "oauth2"
    OIDC4VP = "oidc4vp"


class InteractionTypes(EnumListMixin):
    """Enumeration of interaction types."""

    PROPERTY = "Property"
    ACTION = "Action"
    EVENT = "Event"
