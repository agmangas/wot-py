#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent all interaction patterns.
"""

from abc import ABCMeta

# noinspection PyPackageRequirements
from slugify import slugify

from wotpy.td.enums import InteractionTypes
from wotpy.td.validation import is_valid_safe_name


class InteractionPattern(object):
    """A functionality exposed by Thing that is defined by the TD Interaction Model."""

    __metaclass__ = ABCMeta

    def __init__(self, thing, **kwargs):
        self.thing = thing
        self.id = kwargs.pop("id")
        self.label = kwargs.get("label")
        self.description = kwargs.get("description")
        self._forms = []

        if not is_valid_safe_name(self.id):
            raise ValueError("Invalid Interaction ID: {}".format(self.id))

    @property
    def name(self):
        """Interaction name."""

        return self.id

    @property
    def url_name(self):
        """URL-safe version of the name."""

        return slugify(self.id)

    @property
    def forms(self):
        """Sequence of forms linked to this interaction."""

        return self._forms[:]

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
    """The Property interaction definitions (also see Property vocabulary
    definition section) provides metadata for readable and/or writeable data
    that can be static (e.g., supported mode, rated output voltage, etc.) or
    dynamic (e.g., current fill level of water, minimum recorded temperature, etc.)."""

    def __init__(self, thing, **kwargs):
        super(Property, self).__init__(thing, **kwargs)
        self.data_schema = kwargs.pop("data_schema")
        self.observable = kwargs.get("observable", False)
        self.writable = kwargs.get("writable", False)

    @property
    def interaction_type(self):
        """Interaction type."""

        return InteractionTypes.PROPERTY


class Action(InteractionPattern):
    """The Action interaction pattern (also see Action vocabulary definition section)
    targets changes or processes on a Thing that take a certain time to complete
    (i.e., actions cannot be applied instantaneously like property writes). """

    def __init__(self, thing, **kwargs):
        super(Action, self).__init__(thing, **kwargs)
        self.input = kwargs.get("input")
        self.output = kwargs.get("output")

    @property
    def interaction_type(self):
        """Interaction type."""

        return InteractionTypes.ACTION


class Event(InteractionPattern):
    """The Event interaction pattern (also see Event vocabulary definition section)
    enables a mechanism to be notified by a Thing on a certain condition."""

    def __init__(self, thing, **kwargs):
        super(Event, self).__init__(thing, **kwargs)
        self.data_schema = kwargs.pop("data_schema")

    @property
    def interaction_type(self):
        """Interaction type."""

        return InteractionTypes.EVENT
