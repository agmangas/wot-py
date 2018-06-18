#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent Interaction instances accessed on a ExposedThing.
"""

import tornado.gen
from six.moves import UserDict


class ExposedThingProperty(object):
    """The ThingProperty interface implementation for ExposedThing objects.
    Used to represent Thing Property interactions."""

    def __init__(self, exposed_thing, name):
        self._exposed_thing = exposed_thing
        self._name = name

    @tornado.gen.coroutine
    def get(self):
        """The get() method will fetch the value of the Property.
        A coroutine that yields the value or raises an error."""

        value = yield self._exposed_thing.read_property(self._name)
        raise tornado.gen.Return(value)

    @tornado.gen.coroutine
    def set(self, value):
        """The set() method will attempt to set the value of the
        Property specified in the value argument whose type SHOULD
        match the one specified by the type property.
        A coroutine that yields on success or raises an error."""

        yield self._exposed_thing.write_property(self._name, value)

    def subscribe(self, *args, **kwargs):
        """Subscribe to an stream of events emitted when the property value changes."""

        return self._exposed_thing.on_property_change(self._name).subscribe(*args, **kwargs)


class ExposedThingPropertyDict(UserDict):
    """The ThingProperty interface implementation for ExposedThing objects.
    Used to represent Thing Property interactions."""

    def __init__(self, *args, **kwargs):
        self._exposed_thing = kwargs.pop("exposed_thing")
        UserDict.__init__(self, *args, **kwargs)

    def __getitem__(self, name):
        if name not in self._exposed_thing.thing.properties:
            raise KeyError("Unknown property: {}".format(name))

        return ExposedThingProperty(self._exposed_thing, name)
