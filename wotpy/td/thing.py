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

from wotpy.td.interaction import Property, Action, Event
from wotpy.wot.dictionaries.wot import ThingTemplateDict


class Thing(object):
    """An abstraction of a physical or virtual entity whose metadata
    and interfaces are described by a WoT Thing Description."""

    def __init__(self, thing_template=None, **kwargs):
        self._thing_templt = thing_template if thing_template else ThingTemplateDict(**kwargs)
        self._properties = {}
        self._actions = {}
        self._events = {}
        self._init_template_interactions()

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal ThingTemplate dict before propagating the exception."""

        return getattr(self._thing_templt, name)

    def _init_template_interactions(self):
        """Adds the interactions declared in the ThingTemplate to the instance private dicts."""

        for name, property_init in six.iteritems(self.thing_template.properties):
            prop = Property(thing=self, name=name, init_dict=property_init)
            self.add_interaction(prop)

        for name, action_init in six.iteritems(self.thing_template.actions):
            action = Action(thing=self, name=name, init_dict=action_init)
            self.add_interaction(action)

        for name, event_init in six.iteritems(self.thing_template.events):
            event = Event(thing=self, name=name, init_dict=event_init)
            self.add_interaction(event)

    @property
    def thing_template(self):
        """The ThingTemplate dictionary of this Thing."""

        return self._thing_templt

    @property
    def id(self):
        """Thing ID."""

        return self.thing_template.id

    @property
    def name(self):
        """Thing name."""

        return self.thing_template.name

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

        name_raw = self.thing_template.to_dict().get("name")

        return slugify("{}-{}".format(name_raw, self.uuid)) if name_raw else self.uuid

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

    @property
    def security(self):
        """Returns a list of SecurityScheme objects that represents
        the security strategies implemented on this Thing."""

        return None

    def find_interaction(self, name):
        """Finds an existing Interaction by name.
        The name argument may be the original name or the URL-safe version."""

        def is_match(intrct):
            return intrct.name == name or intrct.url_name == name

        return next((intrct for intrct in self.interactions if is_match(intrct)), None)

    def add_interaction(self, interaction):
        """Add a new Interaction."""

        assert isinstance(interaction, (Property, Event, Action))
        assert interaction.thing is self

        if self.find_interaction(interaction.name) is not None:
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
