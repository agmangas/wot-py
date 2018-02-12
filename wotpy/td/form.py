#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.td.jsonld.form import JsonLDForm


class Form(object):
    """Communication metadata where a service can be accessed by a client application."""

    def __init__(self, interaction, protocol, href, media_type,
                 rel=None, protocol_options=None, **kwargs):
        self.interaction = interaction
        self.protocol = protocol
        self.href = href
        self.media_type = media_type
        self.rel = rel
        self.protocol_options = protocol_options
        self.metadata = kwargs

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

        if self.protocol_options is not None:
            ret.update(self.protocol_options)

        if len(self.metadata):ret.update(self.metadata)

        return ret

    def to_jsonld_form(self):
        """Returns an instance of JsonLDForm that is a wrapper for
        the JSON-LD dictionary that represents this Form."""

        return JsonLDForm(doc=self.to_jsonld_dict())
