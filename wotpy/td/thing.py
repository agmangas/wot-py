#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings

from wotpy.utils.strings import clean_str
from wotpy.td.constants import WOT_CONTEXT_URL
from wotpy.td.jsonld.thing import JsonLDThingDescription


class Thing(object):
    """Describes a physical and/or virtual Thing (may represent one or
    more physical and / or virtual Things) in the Web of Thing context."""

    def __init__(self, name, security=None, base=None):
        clean_name = clean_str(name)

        if clean_name != name:
            warnings.warn("Unsafe name \"{}\" (using clean: \"{}\")".format(name, clean_name))

        self._name = clean_name
        self.security = security
        self.base = base
        self._interactions = []
        self._types = []
        self._meta = {}
        self._contexts = [WOT_CONTEXT_URL]

    def __cmp__(self, other):
        is_equal = self.name == other.name

        if is_equal:
            return 0

        return 1 if self.name > other.name else -1

    def __hash__(self):
        return hash(self.name)

    @property
    def name(self):
        """Name property."""

        return self._name

    @property
    def interaction(self):
        """Interaction property."""

        return self._interactions

    @property
    def type(self):
        """Type property."""

        return self._types

    def add_context(self, context_url, context_prefix=None):
        """Add a new context with an optional prefix."""

        if context_prefix:
            self._contexts.append({context_prefix: context_url})
        else:
            self._contexts.append(context_url)

    def add_interaction(self, interaction):
        """Add a new Link."""

        if interaction in self._interactions:
            raise ValueError("Already existing Interaction")

        self._interactions.append(interaction)

    def remove_interaction(self, interaction):
        """Remove an existing Link."""

        try:
            pop_idx = self._interactions.index(interaction)
            self._interactions.pop(pop_idx)
        except ValueError:
            pass

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

    def add_meta(self, key, val):
        """Add a new metadata key-value pair."""

        self._meta[key] = val

    def remove_meta(self, key):
        """Remove an existing metadata key-value pair."""

        try:
            self._meta.pop(key)
        except KeyError:
            pass

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = {
            "@context": self._contexts,
            "@type": self.type,
            "name": self.name,
            "interaction": [item.to_jsonld_dict() for item in self.interaction]
        }

        if self.base:
            doc.update({"base": self.base})

        if self.security:
            doc.update({"security": self.security})

        doc.update(self._meta)

        return doc

    def to_jsonld_thing_description(self):
        """Returns an instance of JsonLDThingDescription that is a
        wrapper for the JSON-LD dictionary that represents this Thing."""

        return JsonLDThingDescription(doc=self.to_jsonld_dict())
