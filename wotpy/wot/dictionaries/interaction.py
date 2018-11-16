#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for dictionaries for interaction initialization that are defined in the Scripting API.
"""

import six

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.wot.dictionaries.link import FormDict
from wotpy.wot.dictionaries.schema import DataSchemaDict
from wotpy.wot.dictionaries.security import SecuritySchemeDict


class InteractionFragmentDict(WotBaseDict):
    """Base class for the three types of Interaction patterns
    (Properties, Actions and Events)."""

    class Meta:
        fields = {
            "forms",
            "title",
            "uriVariables",
            "description",
            "security",
            "scopes"
        }

    @property
    def forms(self):
        """Indicates one or more endpoints from which
        an interaction pattern is accessible."""

        return [FormDict(item) for item in self._init.get("forms", [])]

    @property
    def uri_variables(self):
        """Define URI template variables as collection based on DataSchema declarations."""

        if "uriVariables" not in self._init:
            return None

        return {
            key: DataSchemaDict.build(val)
            for key, val in six.iteritems(self._init.get("uriVariables"))
        }

    @property
    def security(self):
        """Set of security configurations, provided as an array,
        that must all be satisfied for access to resources at or
        below the current level, if not overridden at a lower level."""

        if "security" not in self._init:
            return None

        return [SecuritySchemeDict.build(item) for item in self._init.get("security")]


class PropertyFragmentDict(InteractionFragmentDict):
    """A dictionary wrapper class that contains data to initialize a Property."""

    class Meta:
        fields = InteractionFragmentDict.Meta.fields.union({
            "observable"
        })

    def __init__(self, *args, **kwargs):
        super(PropertyFragmentDict, self).__init__(*args, **kwargs)
        self._data_schema = DataSchemaDict.build(self._init)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal ValueType before propagating the exception."""

        try:
            return super(PropertyFragmentDict, self).__getattr__(name)
        except AttributeError:
            return getattr(self.data_schema, name)

    def to_dict(self):
        """Returns the pure dict (JSON-serializable) representation of this WoT dictionary."""

        ret = super(PropertyFragmentDict, self).to_dict()
        ret.update(self.data_schema.to_dict())

        return ret

    @property
    def data_schema(self):
        """The DataSchema that represents the schema of this property."""

        return self._data_schema

    @property
    def writable(self):
        """Returns True if this Property is writable."""

        return not self.data_schema.read_only


class ActionFragmentDict(InteractionFragmentDict):
    """A dictionary wrapper class that contains data to initialize an Action."""

    class Meta:
        fields = InteractionFragmentDict.Meta.fields.union({
            "input",
            "output",
            "safe",
            "idempotent"
        })

        defaults = {
            "safe": False,
            "idempotent": False
        }

    @property
    def input(self):
        """Used to define the input data schema of the action."""

        init = self._init.get("input")

        return DataSchemaDict.build(init) if init else None

    @property
    def output(self):
        """Used to define the output data schema of the action."""

        init = self._init.get("output")

        return DataSchemaDict.build(init) if init else None


class EventFragmentDict(InteractionFragmentDict):
    """A dictionary wrapper class that contains data to initialize an Event."""

    class Meta:
        fields = InteractionFragmentDict.Meta.fields.union({
            "subscription",
            "data",
            "cancellation"
        })

    @property
    def subscription(self):
        """Defines data that needs to be passed upon subscription,
        e.g., filters or message format for setting up Webhooks."""

        init = self._init.get("subscription")

        return DataSchemaDict.build(init) if init else None

    @property
    def data(self):
        """Defines the data schema of the Event instance messages pushed by the Thing."""

        init = self._init.get("data")

        return DataSchemaDict.build(init) if init else None

    @property
    def cancellation(self):
        """Defines any data that needs to be passed to cancel a subscription,
        e.g., a specific message to remove a Webhook."""

        init = self._init.get("cancellation")

        return DataSchemaDict.build(init) if init else None
