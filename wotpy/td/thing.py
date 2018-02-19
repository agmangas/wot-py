#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.td.constants import WOT_TD_CONTEXT_URL, WOT_COMMON_CONTEXT_URL
from wotpy.td.jsonld.thing import JsonLDThingDescription
from wotpy.td.semantic import ThingSemanticContext, ThingSemanticMetadata, ThingSemanticTypes
from wotpy.utils.strings import clean_str


class Thing(object):
    """Describes a physical and/or virtual Thing (may represent one or
    more physical and / or virtual Things) in the Web of Thing context."""

    def __init__(self, name):
        self.name = clean_str(name, warn=True)
        self.base = None
        self._interactions = []

        self.semantic_types = ThingSemanticTypes()
        self.semantic_metadata = ThingSemanticMetadata()
        self.semantic_context = ThingSemanticContext()
        self.semantic_context.add(context_url=WOT_TD_CONTEXT_URL)
        self.semantic_context.add(context_url=WOT_COMMON_CONTEXT_URL)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @property
    def interactions(self):
        """Sequence of interactions linked to this thing."""

        return self._interactions

    @property
    def types(self):
        """Types of this Thing."""

        return self.semantic_types.to_list()

    def find_interaction(self, name, interaction_type=None):
        """Returns the Interaction that matches the given name."""

        def _is_match(intrct):
            equal_name = intrct.name == name
            type_match = True if not interaction_type else interaction_type in intrct.types
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
            "@context": self.semantic_context.to_jsonld_list(),
            "@type": self.semantic_types.to_list(),
            "name": self.name,
            "interaction": [item.to_jsonld_dict() for item in self.interactions]
        }

        if self.base:
            doc.update({"base": self.base})

        doc.update(self.semantic_metadata.to_dict())

        return doc

    def to_jsonld_thing_description(self):
        """Returns an instance of JsonLDThingDescription that is a
        wrapper for the JSON-LD dictionary that represents this Thing."""

        return JsonLDThingDescription(doc=self.to_jsonld_dict())
