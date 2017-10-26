#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.wot.enums import ThingEventType


class Event(object):
    """Base event class.
    Represents a generic event defined in a TD."""

    def __init__(self, data):
        self._data = data

    @property
    def data(self):
        """Data property."""

        return self._data

    @property
    def event_type(self):
        """Event type property."""

        return ThingEventType.GENERIC_EVENT


class PropertyChangeEvent(Event):
    """Event triggered to indicate a property change.
    Should be initialized with a PropertyChangeEventInit instance."""

    @property
    def event_type(self):
        """Event type property."""

        return ThingEventType.PROPERTY_CHANGE


class ActionInvocationEvent(Event):
    """Event triggered to indicate an action invocation.
    Should be initialized with a ActionInvocationEventInit instance."""

    @property
    def event_type(self):
        """Event type property."""

        return ThingEventType.ACTION_INVOCATION


class ThingDescriptionChangeEvent(Event):
    """Event triggered to indicate a thing description change.
    Should be initialized with a ThingDescriptionChangeEventInit instance."""

    @property
    def event_type(self):
        """Event type property."""

        return ThingEventType.DESCRIPTION_CHANGE
