#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.wot.interfaces.event import AbstractEvent
from wotpy.wot.dictionaries import \
    PropertyChangeEventInit, \
    ActionInvocationEventInit, \
    ThingDescriptionChangeEventInit


class PropertyChangeEvent(AbstractEvent):
    """Event triggered to indicate a property change."""

    def __init__(self, data):
        assert isinstance(data, PropertyChangeEventInit)
        self._data = data

    @property
    def data(self):
        """Data property getter."""

        return self._data


class ActionInvocationEvent(AbstractEvent):
    """Event triggered to indicate an action invocation."""

    def __init__(self, data):
        assert isinstance(data, ActionInvocationEventInit)
        self._data = data

    @property
    def data(self):
        """Data property getter."""

        return self._data


class ThingDescriptionChangeEvent(AbstractEvent):
    """Event triggered to indicate a thing description change."""

    def __init__(self, data):
        assert isinstance(data, ThingDescriptionChangeEventInit)
        self._data = data

    @property
    def data(self):
        """Data property getter."""

        return self._data
