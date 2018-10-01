#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that subscribes to all the Interactions of one kind for
all the ExposedThings contained by a Protocol Binding server.
"""

import six

from wotpy.td.enums import InteractionTypes


class InteractionsSubscriber(object):
    """Class that subscribes to all the Interactions of one kind for
    all the ExposedThings contained by a Protocol Binding server."""

    def __init__(self, interaction_type, server, on_next_builder):
        assert interaction_type in [InteractionTypes.PROPERTY, InteractionTypes.EVENT]
        self._interaction_type = interaction_type
        self._server = server
        self._on_next_builder = on_next_builder
        self._subs = {}

    def _dispose_exposed_thing_subs(self, exp_thing):
        """Disposes of all currently active subscriptions for the given ExposedThing."""

        if exp_thing not in self._subs:
            return

        for key in self._subs[exp_thing]:
            self._subs[exp_thing][key].dispose()

        self._subs.pop(exp_thing)

    def _interaction_attr_name(self):
        """Returns the attribute name of the Thing and ExposedThing
        iterator for the current type of interactions."""

        return {
            InteractionTypes.PROPERTY: "properties",
            InteractionTypes.EVENT: "events"
        }.get(self._interaction_type)

    def _refresh_exposed_thing_subs(self, exp_thing):
        """Refresh the subscriptions for the given ExposedThing."""

        if exp_thing not in self._subs:
            self._subs[exp_thing] = {}

        thing_subs = self._subs[exp_thing]

        attr = self._interaction_attr_name()

        intrc_expected = set(six.itervalues(exp_thing.thing.__getattribute__(attr)))
        intrc_current = set(thing_subs.keys())
        intrc_remove = intrc_current.difference(intrc_expected)

        for intrc in intrc_remove:
            thing_subs[intrc].dispose()
            thing_subs.pop(intrc)

        intrc_new = [item for item in intrc_expected if item not in thing_subs]

        for intrc in intrc_new:
            on_next = self._on_next_builder(exp_thing, intrc)
            thing_subs[intrc] = exp_thing.__getattribute__(attr)[intrc.name].subscribe(on_next)

    def dispose(self):
        """Disposes of all the currently active subscriptions."""

        for exp_thing in list(six.iterkeys(self._subs)):
            self._dispose_exposed_thing_subs(exp_thing)

    def refresh(self):
        """Refresh all subscriptions for the entire set of ExposedThings."""

        things_expected = set(self._server.exposed_things)
        things_current = set(self._subs.keys())
        things_remove = things_current.difference(things_expected)

        for exp_thing in things_remove:
            self._dispose_exposed_thing_subs(exp_thing)

        for exp_thing in things_expected:
            self._refresh_exposed_thing_subs(exp_thing)
