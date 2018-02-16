#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.wot.enums import DefaultThingEvent


class EmittedEvent(object):
    """Base event class.
    Represents a generic event defined in a TD."""

    def __init__(self, init, name):
        self.init = init
        self.name = name

    @property
    def data(self):
        """Data property."""

        return self.init


class PropertyChangeEmittedEvent(EmittedEvent):
    """Event triggered to indicate a property change.
    Should be initialized with a PropertyChangeEventInit instance."""

    def __init__(self, init):
        name = DefaultThingEvent.PROPERTY_CHANGE
        super(PropertyChangeEmittedEvent, self).__init__(init=init, name=name)


class ActionInvocationEmittedEvent(EmittedEvent):
    """Event triggered to indicate an action invocation.
    Should be initialized with a ActionInvocationEventInit instance."""

    def __init__(self, init):
        name = DefaultThingEvent.ACTION_INVOCATION
        super(ActionInvocationEmittedEvent, self).__init__(init=init, name=name)


class ThingDescriptionChangeEmittedEvent(EmittedEvent):
    """Event triggered to indicate a thing description change.
    Should be initialized with a ThingDescriptionChangeEventInit instance."""

    def __init__(self, init):
        name = DefaultThingEvent.DESCRIPTION_CHANGE
        super(ThingDescriptionChangeEmittedEvent, self).__init__(init=init, name=name)
