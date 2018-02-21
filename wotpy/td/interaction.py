#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent all interaction patterns.
"""

from abc import ABCMeta, abstractmethod

# noinspection PyPackageRequirements
from slugify import slugify

from wotpy.td.enums import InteractionTypes
from wotpy.td.semantic import ThingSemanticMetadata, ThingSemanticTypes
from wotpy.utils.strings import is_safe_name


class InteractionPattern(object):
    """A functionality exposed by Thing that is defined by the TD Interaction Model."""

    __metaclass__ = ABCMeta

    def __init__(self, thing, name):
        if not is_safe_name(name):
            raise ValueError("Unsafe Interaction name: {}".format(name))

        self.thing = thing
        self.name = name
        self._forms = []

        self.semantic_types = ThingSemanticTypes()
        self.semantic_metadata = ThingSemanticMetadata()

    @property
    def id(self):
        """Returns the ID of this Interaction.
        The ID is a hash that is based on its URL-safe name and the ID of its Thing.
        No two Interactions with the same ID may exist within the same Thing."""

        return hash((self.thing.id, self.url_name))

    @property
    def url_name(self):
        """URL-safe version of the name."""

        return slugify(self.name)

    @property
    def forms(self):
        """Sequence of forms linked to this interaction."""

        return self._forms[:]

    @property
    def types(self):
        """Type property."""

        return self.semantic_types.to_list()

    def add_form(self, form):
        """Add a new Form."""

        assert form.interaction is self

        exists_id = next((True for item in self._forms if item.id == form.id), False)

        if exists_id:
            raise ValueError("Duplicated Form: {}".format(form))

        self._forms.append(form)

    def remove_form(self, form):
        """Remove an existing Form."""

        try:
            pop_idx = self._forms.index(form)
            self._forms.pop(pop_idx)
        except ValueError:
            pass

    def _build_base_jsonld_dict(self):
        """Builds and returns the base InteractionPattern JSON-LD dict."""

        doc = {
            "@type": self.semantic_types.to_list(),
            "name": self.name,
            "form": [item.to_jsonld_dict() for item in self.forms]
        }

        doc.update(self.semantic_metadata.to_dict())

        return doc

    @abstractmethod
    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        pass


class Property(InteractionPattern):
    """The Property interaction definitions (also see Property vocabulary
    definition section) provides metadata for readable and/or writeable data
    that can be static (e.g., supported mode, rated output voltage, etc.) or
    dynamic (e.g., current fill level of water, minimum recorded temperature, etc.)."""

    def __init__(self, thing, name, output_data, observable=False, writable=False):
        super(Property, self).__init__(thing, name)
        self.semantic_types.add(InteractionTypes.PROPERTY)
        self.output_data = output_data
        self.observable = True if observable else False
        self.writable = True if writable else False

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = self._build_base_jsonld_dict()

        doc.update({
            "outputData": self.output_data,
            "observable": self.observable,
            "writable": self.writable
        })

        return doc


class Action(InteractionPattern):
    """The Action interaction pattern (also see Action vocabulary definition section)
    targets changes or processes on a Thing that take a certain time to complete
    (i.e., actions cannot be applied instantaneously like property writes). """

    def __init__(self, thing, name, output_data=None, input_data=None):
        super(Action, self).__init__(thing, name)
        self.semantic_types.add(InteractionTypes.ACTION)
        self.output_data = output_data
        self.input_data = input_data

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = self._build_base_jsonld_dict()

        if self.output_data is not None:
            doc.update({"outputData": self.output_data})

        if self.input_data is not None:
            doc.update({"inputData": self.input_data})

        return doc


class Event(InteractionPattern):
    """The Event interaction pattern (also see Event vocabulary definition section)
    enables a mechanism to be notified by a Thing on a certain condition."""

    def __init__(self, thing, name, output_data):
        super(Event, self).__init__(thing, name)
        self.semantic_types.add(InteractionTypes.EVENT)
        self.output_data = output_data

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = self._build_base_jsonld_dict()

        doc.update({
            "outputData": self.output_data
        })

        return doc
