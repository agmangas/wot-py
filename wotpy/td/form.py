#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the form entities exposed by interactions.
"""

from wotpy.td.semantic import ThingSemanticMetadata


class Form(object):
    """Communication metadata where a service can be accessed by a client application."""

    def __init__(self, interaction, protocol, href, media_type, rel=None):
        self.interaction = interaction
        self.protocol = protocol
        self.href = href
        self.media_type = media_type
        self.rel = rel

        self.semantic_metadata = ThingSemanticMetadata()

    @property
    def id(self):
        """Returns the ID of this Form.
        The ID is a hash that is based on its attributes and the ID of its Interaction.
        No two Forms with the same ID may exist within the same Interaction."""

        return hash((
            self.interaction.id,
            self.protocol,
            self.href,
            self.media_type,
            self.rel
        ))

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        ret = {
            "href": self.href,
            "mediaType": self.media_type
        }

        if self.rel is not None:
            ret.update({"rel": self.rel})

        ret.update(self.semantic_metadata.to_dict())

        return ret
