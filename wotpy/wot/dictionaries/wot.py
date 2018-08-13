#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for dictionaries used at the WoT object level defined in the Scripting API.
"""

import six

from wotpy.wot.dictionaries.interaction import PropertyFragment, ActionFragment, EventFragment
from wotpy.wot.dictionaries.link import WebLinkDict
from wotpy.wot.dictionaries.security import SecuritySchemeDict
from wotpy.wot.dictionaries.utils import build_init_dict


class ThingFragment(object):
    """ThingTemplate is a wrapper around a dictionary that contains properties
    representing semantic metadata and interactions (Properties, Actions and Events).
    It is used for initializing an internal representation of a Thing Description,
    and it is also used in ThingFilter."""

    def __init__(self, *args, **kwargs):
        self._init = build_init_dict(args, kwargs)

        if self.id is None:
            raise ValueError("Thing ID is required")

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return self._init

    @property
    def name(self):
        """The name attribute represents the name of the Thing."""

        return self._init.get("name", self.id)

    @property
    def id(self):
        """The id optional attribute represents an application provided hint
        for the unique identifier of the Thing, typically a URI, IRI, or URN.
        Note that the WoT Runtime may override this with a different value when exposing the Thing."""

        return self._init.get("id")

    @property
    def description(self):
        """The description optional attribute represents
        a human readable description of the Thing."""

        return self._init.get("description")

    @property
    def support(self):
        """The support optional attribute represents human
        readable information about the TD maintainer."""

        return self._init.get("support")

    @property
    def security(self):
        """The security optional attribute represents security metadata."""

        return [SecuritySchemeDict.build(item) for item in self._init.get("security", [])]

    @property
    def properties(self):
        """The properties optional attribute represents a dict with keys
        that correspond to Property names and values of type PropertyInit."""

        return {
            key: PropertyFragment(val)
            for key, val in six.iteritems(self._init.get("properties", {}))
        }

    @property
    def actions(self):
        """The actions optional attribute represents a dict with keys
        that correspond to Action names and values of type ActionInit."""

        return {
            key: ActionFragment(val)
            for key, val in six.iteritems(self._init.get("actions", {}))
        }

    @property
    def events(self):
        """The events optional attribute represents a dictionary with keys
        that correspond to Event names and values of type EventInit."""

        return {
            key: EventFragment(val)
            for key, val in six.iteritems(self._init.get("events", {}))
        }

    @property
    def links(self):
        """The links optional attribute represents an array of WebLink objects."""

        return [WebLinkDict(item) for item in self._init.get("links", [])]

    @property
    def context(self):
        """The @context optional attribute represents a semantic context."""

        return self._init.get("@context")

    @property
    def type(self):
        """The @type optional attribute represents a semantic type."""

        return self._init.get("@type")


class ThingFilter(object):
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
