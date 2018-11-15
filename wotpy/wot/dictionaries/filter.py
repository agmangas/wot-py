#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper class for dictionaries to represent Thing filters.
"""

from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.dictionaries.utils import build_init_dict


class ThingFilterDict(object):
    """The ThingFilter dictionary that represents the
    constraints for discovering Things as key-value pairs."""

    def __init__(self, *args, **kwargs):
        self._init = build_init_dict(args, kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return self._init

    @property
    def method(self):
        """The method property represents the discovery type
        that should be used in the discovery process."""

        return self._init.get("method")

    @property
    def url(self):
        """The url property represents additional information for the discovery method,
        such as the URL of the target entity serving the discovery request,
        for instance a Thing Directory (if method is "directory") or a Thing (otherwise)."""

        return self._init.get("url")

    @property
    def query(self):
        """The query property represents a query string accepted by the implementation,
        for instance a SPARQL or JSON query. Support may be implemented locally in the
        WoT Runtime or remotely as a service in a Thing Directory."""

        return self._init.get("query")

    @property
    def fragment(self):
        """The fragment property represents a ThingFragment dictionary used
        for matching property by property against discovered Things."""

        val = self._init.get("fragment")

        return ThingFragment(val) if val is not None else None
