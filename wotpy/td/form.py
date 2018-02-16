#!/usr/bin/env python
# -*- coding: utf-8 -*-

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

    def __eq__(self, other):
        return self.interaction == other.interaction and \
               self.protocol == other.protocol and \
               self.href == other.href and \
               self.media_type == other.media_type

    def __hash__(self):
        return hash((
            self.interaction,
            self.protocol,
            self.href,
            self.media_type
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
