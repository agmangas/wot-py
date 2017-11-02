#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from wotpy.td.jsonld.link import JsonLDLink


class Link(object):
    """Communication metadata where a service can be accessed by a
    client application. An interaction might have more than one link."""

    def __init__(self, interaction, protocol, **kwargs):
        assert json.dumps(kwargs), "Metadata must be JSON-serializable"
        self._interaction = interaction
        self._protocol = protocol
        self._metadata = kwargs

    def __eq__(self, other):
        return self.interaction == other.interaction and \
               self.protocol == other.protocol and \
               set(self.metadata.items()) == set(other.metadata.items())

    def __hash__(self):
        meta_items = sorted(list(self.metadata.items()))
        hash_key = [self.interaction, self.protocol] + meta_items
        return hash(tuple(hash_key))

    @property
    def interaction(self):
        """Interaction property."""

        return self._interaction

    @property
    def protocol(self):
        """Protocol property."""

        return self._protocol

    @property
    def metadata(self):
        """Metadata property."""

        return self._metadata

    def to_jsonld_dict(self):
        """Returns the JSON-LD dict representation for this instance."""

        return self.metadata

    def to_jsonld_link(self):
        """Returns an instance of JsonLDLink that is a wrapper for
        the JSON-LD dictionary that represents this Link."""

        return JsonLDLink(doc=self.to_jsonld_dict())
