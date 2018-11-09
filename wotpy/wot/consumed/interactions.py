#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent Interaction instances accessed on a ConsumedThing.
"""

import six
import tornado.gen
from rx.concurrency import IOLoopScheduler
from six.moves import UserDict


class ConsumedThingInteractionDict(UserDict):
    """A dictionary that provides lazy access to the objects that implement
    the Interaction interface for each interaction in a given ConsumedThing."""

    def __init__(self, *args, **kwargs):
        self._consumed_thing = kwargs.pop("consumed_thing")
        UserDict.__init__(self, *args, **kwargs)

    def __getitem__(self, name):
        """Lazily build and return an object that implements the Interaction interface."""

        if name not in self.thing_interaction_dict:
            raise KeyError("Unknown interaction: {}".format(name))

        return self.thing_interaction_class(self._consumed_thing, name)

    def __len__(self):
        return len(self.thing_interaction_dict)

    def __contains__(self, item):
        return item in self.thing_interaction_dict

    def __iter__(self):
        return six.iterkeys(self.thing_interaction_dict)

    @property
    def thing_interaction_dict(self):
        """Returns an interactions dict by name.
        The dict values are the raw dict interactions as contained in a TD document."""

        raise NotImplementedError()

    @property
    def thing_interaction_class(self):
        """Returns the class that implements the
        Interaction interface for this type of interaction."""

        raise NotImplementedError()


class ConsumedThingPropertyDict(ConsumedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingProperty interface for each property in a given ConsumedThing."""

    @property
    def thing_interaction_dict(self):
        return self._consumed_thing.td.properties

    @property
    def thing_interaction_class(self):
        return ConsumedThingProperty


class ConsumedThingActionDict(ConsumedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingAction interface for each action in a given ConsumedThing."""

    @property
    def thing_interaction_dict(self):
        return self._consumed_thing.td.actions

    @property
    def thing_interaction_class(self):
        return ConsumedThingAction


class ConsumedThingEventDict(ConsumedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingEvent interface for each event in a given ConsumedThing."""

    @property
    def thing_interaction_dict(self):
        return self._consumed_thing.td.events

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

        return getattr(self._consumed_thing.td.properties[self._name], name)

    @tornado.gen.coroutine
    def read(self):
        """The read() method will fetch the value of the Property.
        A coroutine that yields the value or raises an error."""

        value = yield self._consumed_thing.read_property(self._name)
        raise tornado.gen.Return(value)

    @tornado.gen.coroutine
    def write(self, value):
        """The write() method will attempt to set the value of the
        Property specified in the value argument whose type SHOULD
        match the one specified by the type property.
        A coroutine that yields on success or raises an error."""

        yield self._consumed_thing.write_property(self._name, value)

    def subscribe(self, *args, **kwargs):
        """Subscribe to an stream of events emitted when the property value changes."""

        observable = self._consumed_thing.on_property_change(self._name)
        return observable.subscribe_on(IOLoopScheduler()).subscribe(*args, **kwargs)


class ConsumedThingAction(object):
    """The ThingAction interface implementation for ConsumedThing objects."""

    def __init__(self, consumed_thing, name):
        self._consumed_thing = consumed_thing
        self._name = name

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        return getattr(self._consumed_thing.td.actions[self._name], name)

    @tornado.gen.coroutine
    def invoke(self, input_value):
        """The invoke() method when invoked, starts the Action interaction
        with the input value provided by the inputValue argument."""

        result = yield self._consumed_thing.invoke_action(self._name, input_value)
        raise tornado.gen.Return(result)


class ConsumedThingEvent(object):
    """The ThingEvent interface implementation for ConsumedThing objects."""

    def __init__(self, consumed_thing, name):
        self._consumed_thing = consumed_thing
        self._name = name

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        return getattr(self._consumed_thing.td.events[self._name], name)

    def subscribe(self, *args, **kwargs):
        """Subscribe to an stream of emissions of this event."""

        observable = self._consumed_thing.on_event(self._name)
        return observable.subscribe_on(IOLoopScheduler()).subscribe(*args, **kwargs)
