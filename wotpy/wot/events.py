#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent events that are emitted by Things.
"""

import pprint

from wotpy.wot.enums import DefaultThingEvent, TDChangeType, TDChangeMethod


class EmittedEvent(object):
    """Base event class.
    Represents a generic event defined in a TD."""

    def __init__(self, init, name):
        self.init = init
        self.name = name

    def __str__(self):
        try:
            init = pprint.pformat(vars(self.init))
        except TypeError:
            init = self.init

        return "<{}> {} {}".format(self.__class__.__name__, self.name, init)

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


class PropertyChangeEventInit(object):
    """Represents the data contained in a property update event.

    Args:
        name (str): Name of the property.
        value: Value of the property.
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value


class ActionInvocationEventInit(object):
    """Represents the data contained in an action invocation event.

    Args:
        action_name (str): Name of the property.
        return_value: Result returned by the action invocation.
    """

    def __init__(self, action_name, return_value):
        self.action_name = action_name
        self.return_value = return_value


class ThingDescriptionChangeEventInit(object):
    """Represents the data contained in a thing description update event.

    Args:
        td_change_type (str): An item of enumeration :py:class:`.TDChangeType`.
        method (str): An item of enumeration :py:class:`.TDChangeMethod`.
        name (str): Name of the Interaction.
        data: An instance of :py:class:`.ThingPropertyInit`, :py:class:`.ThingActionInit`
            or :py:class:`.ThingEventInit` (or ``None`` if the change did not add a new interaction).
        description (dict): A dict that represents a TD serialized to JSON-LD.
    """

    def __init__(self, td_change_type, method, name, data=None, description=None):
        assert td_change_type in TDChangeType.list()
        assert method in TDChangeMethod.list()

        self.td_change_type = td_change_type
        self.method = method
        self.name = name
        self.data = data
        self.description = description
