#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

from wotpy.td.enums import InteractionTypes
from wotpy.utils.strings import clean_str


class InteractionPattern(object):
    __metaclass__ = ABCMeta

    def __init__(self, thing, name, **kwargs):
        self.thing = thing
        self.name = clean_str(name, warn=True)
        self._types = []
        self._forms = []
        self.metadata = kwargs

    def __eq__(self, other):
        return self.thing == other.thing and \
               self.name == other.name

    def __hash__(self):
        return hash((self.thing, self.name))

    @property
    def type(self):
        """Type property."""

        return self._types

    @property
    def form(self):
        """Indicates the endpoints from which an interaction pattern is accessible."""

        return self._forms

    def add_type(self, val):
        """Add a new type."""

        if val not in self._types:
            self._types.append(val)

    def remove_type(self, val):
        """Remove a type."""

        try:
            pop_idx = self._types.index(val)
            self._types.pop(pop_idx)
        except ValueError:
            pass

    def add_form(self, form):
        """Add a new Form."""

        if form in self._forms:
            raise ValueError("Already existing Form")

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
            "@type": self.type,
            "name": self.name,
            "form": [item.to_jsonld_dict() for item in self.form]
        }

        doc.update(self.metadata)

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
        assert not len(self.type)
        self.add_type(InteractionTypes.PROPERTY)
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
        assert not len(self.type)
        self.add_type(InteractionTypes.ACTION)
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
        assert not len(self.type)
        self.add_type(InteractionTypes.EVENT)
        self.output_data = output_data

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = self._build_base_jsonld_dict()

        doc.update({
            "outputData": self.output_data
        })

        return doc
