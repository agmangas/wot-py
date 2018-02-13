#!/usr/bin/env python
# -*- coding: utf-8 -*-

from six.moves import filter

from wotpy.td.constants import WOT_CONTEXT_URL
from wotpy.td.jsonld.thing import JsonLDThingDescription
from wotpy.utils.strings import clean_str


class Thing(object):
    """Describes a physical and/or virtual Thing (may represent one or
    more physical and / or virtual Things) in the Web of Thing context."""

    def __init__(self, name, security=None, base=None, **kwargs):
        self.name = clean_str(name, warn=True)
        self.security = security
        self.base = base
        self._interactions = []
        self._types = []
        self._contexts = [WOT_CONTEXT_URL]
        self.metadata = kwargs

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @property
    def interaction(self):
        """Interaction property."""

        return self._interactions

    @property
    def type(self):
        """Type property."""

        return self._types

    @property
    def context(self):
        """Context property."""

        return self._contexts

    def add_context(self, context_url, context_prefix=None):
        """Add a new context with an optional prefix."""

        if not context_prefix and context_url in self._contexts:
            return

        ctx_dicts = filter(lambda item: isinstance(item, dict), self._contexts)
        dup_prefix = next((True for dct in ctx_dicts if context_prefix in dct), None)

        if dup_prefix:
            return

        if context_prefix:
            self._contexts.append({context_prefix: context_url})
        else:
            self._contexts.append(context_url)

    def find_interaction(self, name, interaction_type=None):
        """Returns the Interaction that matches the given name."""

        def _is_match(intrct):
            equal_name = intrct.name == name
            type_match = True if not interaction_type else interaction_type in intrct.type
            return equal_name and type_match

        return next((item for item in self._interactions if _is_match(item)), None)

    def add_interaction(self, interaction):
        """Add a new Interaction."""

        if interaction in self._interactions:
            raise ValueError("Already existing Interaction")

        self._interactions.append(interaction)

    def remove_interaction(self, name, interaction_type=None):
        """Remove an existing Interaction by name."""

        interaction_remove = self.find_interaction(name, interaction_type=interaction_type)

        if interaction_remove:
            item_idx = self._interactions.index(interaction_remove)
            self._interactions.pop(item_idx)

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = {
            "@context": self.context,
            "@type": self.type,
            "name": self.name,
            "interaction": [item.to_jsonld_dict() for item in self.interaction]
        }

        if self.base:
            doc.update({"base": self.base})

        if self.security:
            doc.update({"security": self.security})

        doc.update(self.metadata)

        return doc

    def to_jsonld_thing_description(self):
        """Returns an instance of JsonLDThingDescription that is a
        wrapper for the JSON-LD dictionary that represents this Thing."""

        return JsonLDThingDescription(doc=self.to_jsonld_dict())
