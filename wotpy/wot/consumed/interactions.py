#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent Interaction instances accessed on a ConsumedThing.
"""

import tornado.gen
from six.moves import UserDict


class ConsumedThingInteractionDict(UserDict):
    """A dictionary that provides lazy access to the objects that implement
    the Interaction interface for each interaction in a given ConsumedThing."""

    def __init__(self, *args, **kwargs):
        self._consumed_thing = kwargs.pop("consumed_thing")
        UserDict.__init__(self, *args, **kwargs)

    def __getitem__(self, name):
        """Lazily build and return an object that implements the Interaction interface."""

        return None

    @property
    def thing_interaction_class(self):
        """Returns the class that implements the
        Interaction interface for this type of interaction."""

        raise NotImplementedError()


class ConsumedThingPropertyDict(ConsumedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingProperty interface for each property in a given ConsumedThing."""

    @property
    def thing_interaction_class(self):
        return ConsumedThingProperty


class ConsumedThingActionDict(ConsumedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingAction interface for each action in a given ConsumedThing."""

    @property
    def thing_interaction_class(self):
        return ConsumedThingAction


class ConsumedThingEventDict(ConsumedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingEvent interface for each event in a given ConsumedThing."""

    @property
    def thing_interaction_class(self):
        return ConsumedThingEvent


class ConsumedThingProperty(object):
    """The ThingProperty interface implementation for ConsumedThing objects."""

    def __init__(self, consumed_thing, name):
        self._consumed_thing = consumed_thing
        self._name = name

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        raise NotImplementedError()

    @tornado.gen.coroutine
    def get(self):
        """The get() method will fetch the value of the Property.
        A coroutine that yields the value or raises an error."""

        raise NotImplementedError()

    @tornado.gen.coroutine
    def set(self, value):
        """The set() method will attempt to set the value of the
        Property specified in the value argument whose type SHOULD
        match the one specified by the type property.
        A coroutine that yields on success or raises an error."""

        raise NotImplementedError()

    def subscribe(self, *args, **kwargs):
        """Subscribe to an stream of events emitted when the property value changes."""

        raise NotImplementedError()


class ConsumedThingAction(object):
    """The ThingAction interface implementation for ConsumedThing objects."""

    def __init__(self, consumed_thing, name):
        self._consumed_thing = consumed_thing
        self._name = name

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        raise NotImplementedError()

    @tornado.gen.coroutine
    def run(self, input_value):
        """The run() method when invoked, starts the Action interaction
        with the input value provided by the inputValue argument."""

        raise NotImplementedError()


class ConsumedThingEvent(object):
    """The ThingEvent interface implementation for ConsumedThing objects."""

    def __init__(self, consumed_thing, name):
        self._consumed_thing = consumed_thing
        self._name = name

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        raise NotImplementedError()

    def subscribe(self, *args, **kwargs):
        """Subscribe to an stream of emissions of this event."""

        raise NotImplementedError()
