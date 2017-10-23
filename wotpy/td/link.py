#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.td.jsonld.link import JsonLDLink


class Link(object):
    """Communication metadata where a service can be accessed by a
    client application. An interaction might have more than one link."""

    def __init__(self, interaction, href, media_type):
        self._interaction = interaction
        self.href = href
        self.media_type = media_type

    def __eq__(self, other):
        return self.interaction == other.interaction and \
               self.href == other.href and \
               self.media_type == other.media_type

    def __hash__(self):
        return hash((self.interaction, self.href, self.media_type))

    @property
    def interaction(self):
        """Interaction property."""

        return self._interaction

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        doc = {
            "href": self.href,
            "mediaType": self.media_type
        }

        return doc

    def to_jsonld_link(self):
        """Returns an instance of JsonLDLink that is a wrapper for
        the JSON-LD dictionary that represents this Link."""

        return JsonLDLink(doc=self.to_jsonld_dict())
