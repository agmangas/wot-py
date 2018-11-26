#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents a group or set of ExposedThing instances that exist in the same context.
"""


class ExposedThingSet(object):
    """Represents a group of ExposedThing objects.
    A group cannot contain two ExposedThing with the same Thing ID."""

    def __init__(self):
        self._exposed_things = {}

    @property
    def exposed_things(self):
        """A generator that yields all the ExposedThing contained in this group."""

        for exposed_thing in self._exposed_things.values():
            yield exposed_thing

    def contains(self, exposed_thing):
        """Returns True if this group contains the given ExposedThing."""

        return exposed_thing in self._exposed_things.values()

    def add(self, exposed_thing):
        """Add a new ExposedThing to this set."""

        if exposed_thing.thing.id in self._exposed_things:
            raise ValueError("Duplicate Exposed Thing: {}".format(exposed_thing.name))

        self._exposed_things[exposed_thing.thing.id] = exposed_thing

    def remove(self, thing_id):
        """Removes an existing ExposedThing by ID.
        The thing_id argument may be the original Thing ID or the URL-safe name."""

        exposed_thing = self.find_by_thing_id(thing_id)

        if exposed_thing is None:
            raise ValueError("Unknown Exposed Thing: {}".format(thing_id))

        assert exposed_thing.thing.id in self._exposed_things
        self._exposed_things.pop(exposed_thing.thing.id)

    def find_by_thing_id(self, thing_id):
        """Finds an existing ExposedThing by Thing ID.
        The ID argument may be the original Thing ID or the URL-safe name
        (which is also unique and based on the ID)."""

        def is_match(exp_thing):
            return exp_thing.thing.id == thing_id or exp_thing.thing.url_name == thing_id

        return next((item for item in self._exposed_things.values() if is_match(item)), None)

    def find_by_interaction(self, interaction):
        """Finds the ExposedThing whose Thing contains the given Interaction."""

        def is_match(exp_thing):
            return exp_thing.thing is interaction.thing

        return next((item for item in self._exposed_things.values() if is_match(item)), None)
