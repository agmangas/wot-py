#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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
            raise ValueError("Duplicate Exposed Thing: {}".format(exposed_thing.title))

        self._exposed_things[exposed_thing.thing.id] = exposed_thing

    def remove(self, thing_id):
        """Removes an existing ExposedThing by ID.
        The thing_id argument may be the original Thing ID or the URL-safe name."""

        exposed_thing = self.find_by_thing_id(thing_id)

        if exposed_thing is None or exposed_thing.thing.id not in self._exposed_things:
            raise ValueError("Unknown Exposed Thing: {}".format(thing_id))

        self._exposed_things.pop(exposed_thing.thing.id)

    def find_by_thing_id(self, thing_id):
        """Finds an existing ExposedThing by Thing ID.
        The ID argument may be the original Thing ID or the URL-safe name
        (which is also unique and based on the ID)."""

        def is_match(exp_thing):
            return (
                exp_thing.thing.id == thing_id or exp_thing.thing.url_name == thing_id
            )

        return next(
            (item for item in self._exposed_things.values() if is_match(item)), None
        )

    def find_by_interaction(self, interaction):
        """Finds the ExposedThing whose Thing contains the given Interaction."""

        def is_match(exp_thing):
            return exp_thing.thing is interaction.thing

        return next(
            (item for item in self._exposed_things.values() if is_match(item)), None
        )
