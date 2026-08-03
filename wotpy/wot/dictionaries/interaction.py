#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Wrapper classes for dictionaries for interaction initialization that are defined in the Scripting API.
"""

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.wot.dictionaries.link import FormDict
from wotpy.wot.dictionaries.schema import DataSchemaDict
from wotpy.wot.dictionaries.security import SecuritySchemeDict


class InteractionFragmentDict(WotBaseDict):
    """Base class for the three types of Interaction patterns
    (Properties, Actions and Events)."""

    class Meta:
        fields = {
            "@type",
            "title",
            "titles",
            "description",
            "descriptions",
            "forms",
            "uriVariables"
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
            for key, val in self._init.get("uriVariables").items()
        }


class PropertyFragmentDict(InteractionFragmentDict):
    """A dictionary wrapper class that contains data to initialize a Property."""

    class Meta:
        fields = InteractionFragmentDict.Meta.fields.union({"observable"})

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._data_schema = DataSchemaDict.build(self._init)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal ValueType before propagating the exception."""

        try:
            return super().__getattr__(name)
        except AttributeError:
            return getattr(self.data_schema, name)

    def to_dict(self):
        """Returns the pure dict (JSON-serializable) representation of this WoT dictionary."""

        ret = super().to_dict()
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

    @property
    def forms(self):
        """Indicates one or more endpoints from which
        an interaction pattern is accessible."""

        form_dicts = [FormDict(item) for item in self._init.get("forms", [])]
        for form_dict in form_dicts:
            read_only = bool(self._init.get("readOnly"))
            write_only = bool(self._init.get("writeOnly"))

            if not read_only and not write_only:
                form_dict.Meta.defaults["op"] = [
                    "readproperty",
                    "writeproperty"
                ]
            elif read_only:
                form_dict.Meta.defaults["op"] = ["readproperty"]
            elif write_only:
                form_dict.Meta.defaults["op"] = ["writeproperty"]

        return form_dicts


class ActionFragmentDict(InteractionFragmentDict):
    """A dictionary wrapper class that contains data to initialize an Action."""

    class Meta:
        fields = InteractionFragmentDict.Meta.fields.union({
            "input",
            "output",
            "safe",
            "idempotent",
            "synchronous"
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

    @property
    def forms(self):
        """Indicates one or more endpoints from which
        an interaction pattern is accessible."""

        form_dicts = [FormDict(item) for item in self._init.get("forms", [])]
        for form_dict in form_dicts:
            form_dict.Meta.defaults["op"] = "invokeaction"
        return form_dicts


class EventFragmentDict(InteractionFragmentDict):
    """A dictionary wrapper class that contains data to initialize an Event."""

    class Meta:
        fields = InteractionFragmentDict.Meta.fields.union({
            "subscription",
            "data",
            "dataResponse",
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
    def data_response(self):
        """Defines the data schema of the Event response messages sent by the
        consumer in a response to a data message."""

        init = self._init.get("dataResponse")

        return DataSchemaDict.build(init) if init else None

    @property
    def cancellation(self):
        """Defines any data that needs to be passed to cancel a subscription,
        e.g., a specific message to remove a Webhook."""

        init = self._init.get("cancellation")

        return DataSchemaDict.build(init) if init else None

    @property
    def forms(self):
        """Indicates one or more endpoints from which
        an interaction pattern is accessible."""

        form_dicts = [FormDict(item) for item in self._init.get("forms", [])]
        for form_dict in form_dicts:
            form_dict.Meta.defaults["op"] = [
                "subscribeevent",
                "unsubscribeevent"
            ]
        return form_dicts
