#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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
Classes that represent Interaction instances accessed on a ExposedThing.
"""

from collections import UserDict

from reactivex.scheduler.eventloop import IOLoopScheduler
from slugify import slugify
from tornado import ioloop


class ExposedThingInteractionDict(UserDict):
    """A dictionary that provides lazy access to the objects that implement
    the Interaction interface for each interaction in a given ExposedThing."""

    def __init__(self, *args, **kwargs):
        self._exposed_thing = kwargs.pop("exposed_thing")
        UserDict.__init__(self, *args, **kwargs)

    def _find_normalized_name(self, name):
        """Takes a case-insensitive URL-safe interaction name and returns
        the actual name in the interaction dict."""

        return next((key for key in self.interaction_dict.keys() if slugify(key) == slugify(name)), None)

    def __getitem__(self, name):
        """Lazily build and return an object that implements the Interaction interface."""

        name_normalized = self._find_normalized_name(name)

        if name_normalized is None:
            raise KeyError("Unknown interaction: {}".format(name))

        return self.thing_interaction_class(self._exposed_thing, name_normalized)

    def __len__(self):
        return len(self.interaction_dict)

    def __contains__(self, item):
        return self._find_normalized_name(item) is not None

    def __iter__(self):
        return iter(self.interaction_dict.keys())

    @property
    def interaction_dict(self):
        """Returns the InteractionPattern objects dict by name."""

        raise NotImplementedError()

    @property
    def thing_interaction_class(self):
        """Returns the class that implements the
        Interaction interface for this type of interaction."""

        raise NotImplementedError()


class ExposedThingPropertyDict(ExposedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingProperty interface for each property in a given ExposedThing."""

    @property
    def interaction_dict(self):
        return self._exposed_thing.thing.properties

    @property
    def thing_interaction_class(self):
        return ExposedThingProperty


class ExposedThingActionDict(ExposedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingAction interface for each action in a given ExposedThing."""

    @property
    def interaction_dict(self):
        return self._exposed_thing.thing.actions

    @property
    def thing_interaction_class(self):
        return ExposedThingAction


class ExposedThingEventDict(ExposedThingInteractionDict):
    """A dictionary that provides lazy access to the objects that implement
    the ThingEvent interface for each event in a given ExposedThing."""

    @property
    def interaction_dict(self):
        return self._exposed_thing.thing.events

    @property
    def thing_interaction_class(self):
        return ExposedThingEvent


class ExposedThingProperty:
    """The ThingProperty interface implementation for ExposedThing objects."""

    def __init__(self, exposed_thing, name):
        self._exposed_thing = exposed_thing
        self._name = name

    def __str__(self):
        return "<{}> ({}::{})".format(
            self.__class__.__name__, self._exposed_thing.id, self._name
        )

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        return getattr(self._exposed_thing.thing.properties[self._name], name)

    async def read(self):
        """The get() method will fetch the value of the Property.
        A coroutine that yields the value or raises an error."""

        value = await self._exposed_thing.read_property(self._name)
        return value

    async def write(self, value):
        """The set() method will attempt to set the value of the
        Property specified in the value argument whose type SHOULD
        match the one specified by the type property.
        A coroutine that yields on success or raises an error."""

        await self._exposed_thing.write_property(self._name, value)

    def subscribe(self, *args, **kwargs):
        """Subscribe to an stream of events emitted when the property value changes."""

        observable = self._exposed_thing.on_property_change(self._name)
        loop = ioloop.IOLoop.current()
        scheduler = IOLoopScheduler(loop)
        kwargs["scheduler"] = scheduler

        return observable.subscribe(*args, **kwargs)


class ExposedThingAction:
    """The ThingAction interface implementation for ExposedThing objects."""

    def __init__(self, exposed_thing, name):
        self._exposed_thing = exposed_thing
        self._name = name

    def __str__(self):
        return "<{}> ({}::{})".format(
            self.__class__.__name__, self._exposed_thing.id, self._name
        )

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        return getattr(self._exposed_thing.thing.actions[self._name], name)

    async def invoke(self, *args):
        """The run() method when invoked, starts the Action interaction
        with the input value provided by the inputValue argument."""

        input_value = args[0] if len(args) else None
        result = await self._exposed_thing.invoke_action(self._name, input_value)
        return result


class ExposedThingEvent:
    """The ThingEvent interface implementation for ExposedThing objects."""

    def __init__(self, exposed_thing, name):
        self._exposed_thing = exposed_thing
        self._name = name

    def __str__(self):
        return "<{}> ({}::{})".format(self.__class__.__name__, self._exposed_thing.id, self._name)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        return getattr(self._exposed_thing.thing.events[self._name], name)

    def subscribe(self, *args, **kwargs):
        """Subscribe to an stream of emissions of this event."""

        observable = self._exposed_thing.on_event(self._name)
        loop = ioloop.IOLoop.current()
        scheduler = IOLoopScheduler(loop)
        kwargs["scheduler"] = scheduler
        
        return observable.subscribe(*args, **kwargs)

    def emit(self, payload):
        """Emits an event that carries data specified by the payload argument."""

        return self._exposed_thing.emit_event(self._name, payload)
