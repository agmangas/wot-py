#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents a Thing.
"""

# noinspection PyPackageRequirements
from slugify import slugify

from wotpy.td.constants import WOT_TD_CONTEXT_URL, WOT_COMMON_CONTEXT_URL
from wotpy.td.jsonld.thing import JsonLDThingDescription
from wotpy.td.semantic import ThingSemanticContext, ThingSemanticMetadata, ThingSemanticTypes
from wotpy.utils.strings import is_safe_name


class Thing(object):
    """An abstraction of a physical or virtual entity whose metadata
    and interfaces are described by a WoT Thing Description."""

    def __init__(self, name):
        if not is_safe_name(name):
            raise ValueError("Unsafe Thing name: {}".format(name))

        self.name = name
        self._interactions = []

        self.semantic_types = ThingSemanticTypes()
        self.semantic_metadata = ThingSemanticMetadata()
        self.semantic_context = ThingSemanticContext()
        self.semantic_context.add(context_url=WOT_TD_CONTEXT_URL)
        self.semantic_context.add(context_url=WOT_COMMON_CONTEXT_URL)

    @property
    def id(self):
        """Returns the ID of this Thing.
        The ID is a hash that is based on its URL-safe name.
        No two Things with the same ID may exist within the same servient."""

        return hash(self.url_name)

    @property
    def url_name(self):
        """URL-safe version of the name."""

        return slugify(self.name)

    @property
    def interactions(self):
        """Sequence of interactions linked to this thing."""

        return self._interactions[:]

    @property
    def types(self):
        """Types of this Thing."""

        return self.semantic_types.to_list()

    def find_interaction(self, name):
        """Finds an existing Interaction by name.
        The name argument may be the original name or the URL-safe version."""

        def is_match(intrct):
            return intrct.name == name or intrct.url_name == name

        return next((item for item in self._interactions if is_match(item)), None)

    def add_interaction(self, interaction):
        """Add a new Interaction."""

        assert interaction.thing is self

        exists_id = next((True for item in self._interactions if item.id == interaction.id), False)

        if exists_id:
            raise ValueError("Duplicated Interaction: {}".format(interaction.name))

        self._interactions.append(interaction)

    def remove_interaction(self, name):
        """Removes an existing Interaction by name.
        The name argument may be the original name or the URL-safe version."""

        interaction = self.find_interaction(name)

        if interaction:
            pop_idx = self._interactions.index(interaction)
            self._interactions.pop(pop_idx)

    def to_jsonld_dict(self, base=None):
        """Returns the JSON-LD dict representation for this instance."""

        doc = {
            "@context": self.semantic_context.to_jsonld_list(),
            "@type": self.semantic_types.to_list(),
            "name": self.name,
            "interaction": [item.to_jsonld_dict() for item in self.interactions]
        }

        if base is not None:
            doc.update({"base": base})

        doc.update(self.semantic_metadata.to_dict())

        return doc

    def to_jsonld_thing_description(self, base=None):
        """Returns an instance of JsonLDThingDescription that is a
        wrapper for the JSON-LD dictionary that represents this Thing."""

        return JsonLDThingDescription(doc=self.to_jsonld_dict(base=base))
