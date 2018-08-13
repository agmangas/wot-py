#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for dictionaries for interaction initialization that are defined in the Scripting API.
"""

from wotpy.wot.dictionaries.schema import DataSchema
from wotpy.wot.dictionaries.utils import build_init_dict


class InteractionFragment(object):
    """A dictionary wrapper class that contains data to initialize an Interaction."""

    def __init__(self, *args, **kwargs):
        self._init = build_init_dict(args, kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties"""

        return {
            "label": self.label,
            "description": self.description
        }

    @property
    def label(self):
        """The label property initializes the text label for the interaction."""

        return self._init.get("label")

    @property
    def description(self):
        """The description property initializes the description for the interaction."""

        return self._init.get("description")


class PropertyFragment(InteractionFragment):
    """A dictionary wrapper class that contains data to initialize a Property."""

    def __init__(self, *args, **kwargs):
        super(PropertyFragment, self).__init__(*args, **kwargs)
        self._data_schema = DataSchema.build(self._init)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal ValueType before propagating the exception."""

        return getattr(self.data_schema, name)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties"""

        base_dict = super(PropertyFragment, self).to_dict()

        base_dict.update({
            "writable": self.writable,
            "observable": self.observable
        })

        base_dict.update(self.data_schema.to_dict())

        return base_dict

    @property
    def data_schema(self):
        """The DataSchemaDictionary wrapper that represents the schema of this interaction."""

        return self._data_schema

    @property
    def writable(self):
        """The writable property initializes access to the Property value.
        The default value is false."""

        return self._init.get("writable", False)

    @property
    def observable(self):
        """The observable property initializes observability access to the Property.
        The default value is false."""

        return self._init.get("observable", False)


class ActionFragment(InteractionFragment):
    """A dictionary wrapper class that contains data to initialize an Action."""

    def __init__(self, *args, **kwargs):
        super(ActionFragment, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties"""

        base_dict = super(ActionFragment, self).to_dict()

        if self.input:
            base_dict.update({"input": self.input.to_dict()})

        if self.output:
            base_dict.update({"output": self.output.to_dict()})

        return base_dict

    @property
    def input(self):
        """The input property initializes the input of type ValueType to the ThingAction.
        Multiple arguments can be provided by applications as an array or as an object."""

        init = self._init.get("input")

        return DataSchema.build(init) if init else None

    @property
    def output(self):
        """The output property initializes the output of type ValueType of the ThingAction.
        The value is overridden when the action is executed."""

        init = self._init.get("output")

        return DataSchema.build(init) if init else None


class EventFragment(PropertyFragment):
    """A dictionary wrapper class that contains data to initialize an Event."""

    pass
