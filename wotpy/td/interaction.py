#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

from wotpy.td.enums import InteractionTypes
from wotpy.td.jsonld.interaction import JsonLDInteraction
from wotpy.utils.strings import clean_str


class InteractionPattern(object):
    __metaclass__ = ABCMeta

    def __init__(self, thing, name):
        self._thing = thing
        self._name = clean_str(name, warn=True)
        self._types = []
        self._links = []
        self._meta = {}

    def __eq__(self, other):
        return self.thing == other.thing and \
               self.name == other.name

    def __hash__(self):
        return hash((self.thing, self.name))

    @property
    def thing(self):
        """Thing property."""

        return self._thing

    @property
    def name(self):
        """Name property."""

        return self._name

    @property
    def type(self):
        """Type property."""

        return self._types

    @property
    def link(self):
        """Link property."""

        return self._links

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

    def add_link(self, link):
        """Add a new Link."""

        if link in self._links:
            raise ValueError("Already existing Link")

        self._links.append(link)

    def remove_link(self, link):
        """Remove an existing Link."""

        try:
            pop_idx = self._links.index(link)
            self._links.pop(pop_idx)
        except ValueError:
            pass

    def add_meta(self, key, val):
        """Add a new metadata key-value pair."""

        self._meta[key] = val

    def remove_meta(self, key):
        """Remove an existing metadata key-value pair."""

        try:
            self._meta.pop(key)
        except KeyError:
            pass

    def _build_base_jsonld_dict(self):
        """Builds and returns the base InteractionPattern JSON-LD dict."""

        doc = {
            "@type": self.type,
            "name": self.name,
            "link": [item.to_jsonld_dict() for item in self.link]
        }

        doc.update(self._meta)

        return doc

    @abstractmethod
    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        pass

    def to_jsonld_interaction(self):
        """Returns an instance of JsonLDInteraction that is a wrapper for
        the JSON-LD dictionary that represents this InteractionPattern."""

        return JsonLDInteraction(doc=self.to_jsonld_dict())


class Property(InteractionPattern):
    """The Property interaction definitions (also see Property vocabulary
    definition section) provides metadata for readable and/or writeable data
    that can be static (e.g., supported mode, rated output voltage, etc.) or
    dynamic (e.g., current fill level of water, minimum recorded temperature, etc.)."""

    def __init__(self, thing, name, output_data, writable=True):
        super(Property, self).__init__(thing, name)
        assert not len(self.type)
        self.add_type(InteractionTypes.PROPERTY)
        self.output_data = output_data
        self.writable = True if writable else False

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = self._build_base_jsonld_dict()

        doc.update({
            "outputData": self.output_data,
            "writable": self.writable
        })

        return doc


class Action(InteractionPattern):
    """The Action interaction pattern (also see Action vocabulary definition section)
    targets changes or processes on a Thing that take a certain time to complete
    (i.e., actions cannot be applied instantaneously like property writes). """

    def __init__(self, thing, name, output_data, input_data):
        super(Action, self).__init__(thing, name)
        assert not len(self.type)
        self.add_type(InteractionTypes.ACTION)
        self.output_data = output_data
        self.input_data = input_data

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = self._build_base_jsonld_dict()

        doc.update({
            "outputData": self.output_data,
            "inputData": self.input_data
        })

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
