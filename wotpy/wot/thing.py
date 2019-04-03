#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents a Thing.
"""

import hashlib
import itertools
import uuid

import six
from slugify import slugify

from wotpy.utils.utils import to_camel
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.interaction import Property, Action, Event


class Thing(object):
    """An abstraction of a physical or virtual entity whose metadata
    and interfaces are described by a WoT Thing Description."""

    THING_FRAGMENT_WRITABLE_FIELDS = {
        "version",
        "name",
        "description",
        "support",
        "created",
        "lastModified",
        "base",
        "links",
        "security"
    }

    assert THING_FRAGMENT_WRITABLE_FIELDS.issubset(ThingFragment.Meta.fields)

    def __init__(self, thing_fragment=None, **kwargs):
        self._thing_fragment = thing_fragment if thing_fragment else ThingFragment(**kwargs)
        self._properties = {}
        self._actions = {}
        self._events = {}
        self._init_fragment_interactions()

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private ThingFragment before propagating the exception."""

        return getattr(self._thing_fragment, name)

    def __setattr__(self, name, value):
        """Setter for ThingFragment attributes."""

        name_camel = to_camel(name)

        if name_camel not in self.THING_FRAGMENT_WRITABLE_FIELDS:
            return super(Thing, self).__setattr__(name, value)

        return self._thing_fragment.__setattr__(name, value)

    def _init_fragment_interactions(self):
        """Adds the interactions declared in the ThingFragment to the instance private dicts."""

        for name, prop_fragment in six.iteritems(self._thing_fragment.properties):
            prop = Property(thing=self, name=name, init_dict=prop_fragment)
            self.add_interaction(prop)

        for name, action_fragment in six.iteritems(self._thing_fragment.actions):
            action = Action(thing=self, name=name, init_dict=action_fragment)
            self.add_interaction(action)

        for name, event_fragment in six.iteritems(self._thing_fragment.events):
            event = Event(thing=self, name=name, init_dict=event_fragment)
            self.add_interaction(event)

    @property
    def thing_fragment(self):
        """The ThingFragment dictionary of this Thing."""

        def interaction_to_json(intrct):
            """Returns the JSON serialization of an Interaction instance."""

            ret = intrct.interaction_fragment.to_dict()

            ret.update({
                "forms": [form.form_dict.to_dict() for form in intrct.forms]
            })

            return ret

        doc = self._thing_fragment.to_dict()

        doc.update({
            "properties": {
                key: interaction_to_json(val)
                for key, val in six.iteritems(self.properties)
            }
        })

        doc.update({
            "actions": {
                key: interaction_to_json(val)
                for key, val in six.iteritems(self.actions)
            }
        })

        doc.update({
            "events": {
                key: interaction_to_json(val)
                for key, val in six.iteritems(self.events)
            }
        })

        return ThingFragment(doc)

    @property
    def id(self):
        """Thing ID."""

        return self.thing_fragment.id

    @property
    def name(self):
        """Thing name."""

        return self.thing_fragment.name

    @property
    def uuid(self):
        """Thing UUID in hex string format (e.g. a5220c5f-6bcb-4675-9c67-a2b1adc280b7).
        This value is deterministic and derived from the Thing ID.
        It may be of use when URL-unsafe chars are not acceptable."""

        hasher = hashlib.md5()
        hasher.update(self.id.encode())
        bytes_id_hash = hasher.digest()

        return str(uuid.UUID(bytes=bytes_id_hash))

    @property
    def url_name(self):
        """Returns the URL-safe name of this Thing.
        The URL name of a Thing is always unique and stable as long as the ID is unique."""

        return slugify("{}-{}".format(self.name, self.uuid))

    @property
    def properties(self):
        """Properties interactions."""

        return self._properties

    @property
    def actions(self):
        """Actions interactions."""

        return self._actions

    @property
    def events(self):
        """Events interactions."""

        return self._events

    @property
    def interactions(self):
        """Sequence of interactions linked to this thing."""

        return itertools.chain(
            self._properties.values(),
            self._actions.values(),
            self._events.values())

    def find_interaction(self, name):
        """Finds an existing Interaction by name.
        The name argument may be the original name or the URL-safe version."""

        def is_match(intrct):
            return intrct.name == name or intrct.url_name == name

        return next((intrct for intrct in self.interactions if is_match(intrct)), None)

    def add_interaction(self, interaction):
        """Add a new Interaction."""

        if not isinstance(interaction, (Property, Event, Action)):
            raise ValueError("Not an Interaction")

        if interaction.thing is not self:
            raise ValueError("Interaction linked to another Thing")

        if self.find_interaction(interaction.name) or self.find_interaction(interaction.url_name):
            raise ValueError("Duplicate Interaction: {}".format(interaction.name))

        interaction_dict_map = {
            Property: self._properties,
            Action: self._actions,
            Event: self._events
        }

        interaction_class = next(
            klass for klass in [Property, Action, Event]
            if isinstance(interaction, klass))

        interaction_dict_map[interaction_class][interaction.name] = interaction

    def remove_interaction(self, name):
        """Removes an existing Interaction by name.
        The name argument may be the original name or the URL-safe version."""

        interaction = self.find_interaction(name)

        if interaction is None:
            return

        self._properties.pop(interaction.name, None)
        self._actions.pop(interaction.name, None)
        self._events.pop(interaction.name, None)
