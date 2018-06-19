#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent all interaction patterns.
"""

from abc import ABCMeta, abstractmethod

# noinspection PyPackageRequirements
from slugify import slugify

from wotpy.td.enums import InteractionTypes
from wotpy.td.validation import is_valid_safe_name
from wotpy.wot.dictionaries import PropertyInitDict, ActionInitDict, EventInitDict


class InteractionPattern(object):
    """A functionality exposed by Thing that is defined by the TD Interaction Model."""

    __metaclass__ = ABCMeta

    def __init__(self, thing, name, init_dict=None, **kwargs):
        if not is_valid_safe_name(name):
            raise ValueError("Invalid Interaction name: {}".format(name))

        self._init_dict = init_dict if init_dict else self.init_class(**kwargs)

        self._thing = thing
        self._name = name
        self._forms = []

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private init dict before propagating the exception."""

        return self._init_dict.__getattribute__(name)

    @property
    @abstractmethod
    def init_class(self):
        """Returns the init dict class for this type of interaction."""

        raise NotImplementedError()

    @property
    def thing(self):
        """Thing that contains this Interaction."""

        return self._thing

    @property
    def name(self):
        """Interaction name.
        No two Interactions with the same name may exist in a Thing."""

        return self._name

    @property
    def url_name(self):
        """URL-safe version of the name."""

        return slugify(self.name)

    @property
    def forms(self):
        """Sequence of forms linked to this interaction."""

        return self._forms

    def add_form(self, form):
        """Add a new Form."""

        assert form.interaction is self

        existing = next((True for item in self._forms if item.id == form.id), False)

        if existing:
            raise ValueError("Duplicate Form: {}".format(form))

        self._forms.append(form)

    def remove_form(self, form):
        """Remove an existing Form."""

        try:
            pop_idx = self._forms.index(form)
            self._forms.pop(pop_idx)
        except ValueError:
            pass


class Property(InteractionPattern):
    """Properties expose internal state of a Thing that can be
    directly accessed (get) and optionally manipulated (set)."""

    @property
    def init_class(self):
        """Returns the init dict class for this type of interaction."""

        return PropertyInitDict

    @property
    def interaction_type(self):
        """Interaction type."""

        return InteractionTypes.PROPERTY


class Action(InteractionPattern):
    """Actions offer functions of the Thing. These functions may manipulate the
    internal state of a Thing in a way that is not possible through setting Properties."""

    @property
    def init_class(self):
        """Returns the init dict class for this type of interaction."""

        return ActionInitDict

    @property
    def interaction_type(self):
        """Interaction type."""

        return InteractionTypes.ACTION


class Event(InteractionPattern):
    """The Event Interaction Pattern describes event sources that asynchronously push messages.
    Here not state, but state transitions (events) are communicated (e.g., clicked)."""

    @property
    def init_class(self):
        """Returns the init dict class for this type of interaction."""

        return EventInitDict

    @property
    def interaction_type(self):
        """Interaction type."""

        return InteractionTypes.EVENT
