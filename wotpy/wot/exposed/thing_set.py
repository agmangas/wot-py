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
Class that represents a group or set of ExposedThing instances that exist in the same context.
"""


class ExposedThingSet:
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

        if exposed_thing.thing.title in self._exposed_things:
            raise ValueError("Duplicate Exposed Thing: {}".format(exposed_thing.title))

        self._exposed_things[exposed_thing.thing.title] = exposed_thing

    def remove(self, thing_title):
        """Removes an existing ExposedThing by title.
        The thing_id argument may be the original Thing title or the URL-safe name."""

        exposed_thing = self.find_by_thing_title(thing_title)

        if exposed_thing is None or exposed_thing.thing.title not in self._exposed_things:
            raise ValueError("Unknown Exposed Thing: {}".format(thing_title))

        self._exposed_things.pop(exposed_thing.thing.title)

    def find_by_thing_title(self, thing_title):
        """Finds an existing ExposedThing by Thing title.
        The ID argument may be the original Thing title or the URL-safe name
        (which is also unique and based on the title)."""

        def is_match(exp_thing):
            return (
                exp_thing.thing.title == thing_title or exp_thing.thing.url_name == thing_title
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
