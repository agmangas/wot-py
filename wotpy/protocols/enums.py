#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to the various protocol servers.
"""

from wotpy.utils.enums import EnumListMixin


class Protocols(EnumListMixin):
    """Enumeration of protocol types."""

    HTTP = "HTTP"
    WEBSOCKETS = "WEBSOCKETS"


class InteractionVerbs(EnumListMixin):
    """Interactions have one or more defined interaction verbs for each
    interaction pattern.  Form Relations allow an interaction to have
    separate protocol mechanisms to support different interaction verbs."""

    READ_PROPERTY = "readProperty"
    WRITE_PROPERTY = "writeProperty"
    OBSERVE_PROPERTY = "observeProperty"
    INVOKE_ACTION = "invokeAction"
    SUBSCRIBE_EVENT = "subscribeEvent"
    UNSUBSCRIBE_EVENT = "unsubscribeEvent"
