#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.wot.enums import DefaultThingEvent


class EmittedEvent(object):
    """Base event class.
    Represents a generic event defined in a TD."""

    def __init__(self, init, name):
        self._name = name
        self._data = init

    @property
    def data(self):
        """Data property."""

        return self._data

    @property
    def name(self):
        """Event name property."""

        return self._name


class PropertyChangeEmittedEvent(EmittedEvent):
    """Event triggered to indicate a property change.
    Should be initialized with a PropertyChangeEventInit instance."""

    # noinspection PyUnusedLocal
    def __init__(self, init):
        super(PropertyChangeEmittedEvent, self).__init__(
            init=init, name=DefaultThingEvent.PROPERTY_CHANGE)


class ActionInvocationEmittedEvent(EmittedEvent):
    """Event triggered to indicate an action invocation.
    Should be initialized with a ActionInvocationEventInit instance."""

    # noinspection PyUnusedLocal
    def __init__(self, init):
        super(ActionInvocationEmittedEvent, self).__init__(
            init=init, name=DefaultThingEvent.ACTION_INVOCATION)


class ThingDescriptionChangeEmittedEvent(EmittedEvent):
    """Event triggered to indicate a thing description change.
    Should be initialized with a ThingDescriptionChangeEventInit instance."""

    # noinspection PyUnusedLocal
    def __init__(self, init):
        super(ThingDescriptionChangeEmittedEvent, self).__init__(
            init=init, name=DefaultThingEvent.DESCRIPTION_CHANGE)
