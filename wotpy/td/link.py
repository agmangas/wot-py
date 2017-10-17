#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.td.jsonld.link import JsonLDLink


class Link(object):
    """Communication metadata where a service can be accessed by a
    client application. An interaction might have more than one link."""

    def __init__(self, href, media_type):
        self.href = href
        self.media_type = media_type

    def __cmp__(self, other):
        is_equal = self.href == other.href and \
                   self.media_type == other.media_type

        if is_equal:
            return 0

        return 1 if self.href > other.href else -1

    def __hash__(self):
        return hash((self.href, self.media_type))

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
