#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper class for dictionaries to represent Things.
"""

import six

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.wot.dictionaries.interaction import PropertyFragmentDict, ActionFragmentDict, EventFragmentDict
from wotpy.wot.dictionaries.link import LinkDict
from wotpy.wot.dictionaries.security import SecuritySchemeDict
from wotpy.utils.utils import to_camel
from wotpy.wot.dictionaries.version import VersioningDict
from wotpy.wot.enums import SecuritySchemeType


class ThingFragment(WotBaseDict):
    """ThingFragment is a wrapper around a dictionary that contains properties
    representing semantic metadata and interactions (Properties, Actions and Events).
    It is used for initializing an internal representation of a Thing Description,
    and it is also used in ThingFilter."""

    class Meta:
        fields = {
            "id",
            "version",
            "name",
            "description",
            "support",
            "created",
            "lastModified",
            "base",
            "properties",
            "actions",
            "events",
            "links",
            "security"
        }

        required = {
            "id"
        }

        fields_readonly = [
            "id"
        ]

        fields_str = [
            "name",
            "description",
            "support",
            "created",
            "lastModified",
            "base"
        ]

        fields_dict = [
            "properties",
            "actions",
            "events"
        ]

        fields_list = [
            "links",
            "security"
        ]

        fields_instance = [
            "version"
        ]

        assert set(fields_readonly + fields_str + fields_dict + fields_list + fields_instance) == fields

    def __setattr__(self, name, value):
        """Checks to see if the attribute that is being set is a
        Thing fragment property and updates the internal dict."""

        name_camel = to_camel(name)

        if name_camel not in self.Meta.fields:
            return super(ThingFragment, self).__setattr__(name, value)

        if name_camel in self.Meta.fields_readonly:
            raise AttributeError("Can't set attribute {}".format(name))

        if name_camel in self.Meta.fields_str:
            self._init[name_camel] = value
            return

        if name_camel in self.Meta.fields_dict:
            self._init[name_camel] = {key: val.to_dict() for key, val in six.iteritems(value)}
            return

        if name_camel in self.Meta.fields_list:
            self._init[name_camel] = [item.to_dict() for item in value]
            return

        if name_camel in self.Meta.fields_instance:
            self._init[name_camel] = value.to_dict()
            return

    @property
    def name(self):
        """The name of the Thing.
        This property returns the ID if the name is undefined."""

        return self._init.get("name", self.id)

    @property
    def security(self):
        """Set of security configurations, provided as an array,
        that must all be satisfied for access to resources at or
        below the current level, if not overridden at a lower level.
        A default nosec security scheme will be provided if none are defined."""

        if "security" not in self._init:
            return [SecuritySchemeDict.build({"scheme": SecuritySchemeType.NOSEC})]

        return [SecuritySchemeDict.build(item) for item in self._init.get("security")]

    @property
    def properties(self):
        """The properties optional attribute represents a dict with keys
        that correspond to Property names and values of type PropertyFragment."""

        return {
            key: PropertyFragmentDict(val)
            for key, val in six.iteritems(self._init.get("properties", {}))
        }

    @property
    def actions(self):
        """The actions optional attribute represents a dict with keys
        that correspond to Action names and values of type ActionFragment."""

        return {
            key: ActionFragmentDict(val)
            for key, val in six.iteritems(self._init.get("actions", {}))
        }

    @property
    def events(self):
        """The events optional attribute represents a dictionary with keys
        that correspond to Event names and values of type EventFragment."""

        return {
            key: EventFragmentDict(val)
            for key, val in six.iteritems(self._init.get("events", {}))
        }

    @property
    def links(self):
        """The links optional attribute represents an array of Link objects."""

        return [LinkDict(item) for item in self._init.get("links", [])]

    @property
    def version(self):
        """Provides version information."""

        return VersioningDict(self._init.get("version")) if self._init.get("version") else None
