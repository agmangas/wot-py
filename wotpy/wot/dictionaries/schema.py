#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for data schema dictionaries defined in the Scripting API.
"""

import six

from wotpy.wot.dictionaries.utils import build_init_dict
from wotpy.wot.enums import JSONType


class DataSchemaDict(object):
    """Represents the common properties of a value type definition."""

    def __init__(self, *args, **kwargs):
        self._init = build_init_dict(args, kwargs)

        if self.type is None:
            raise ValueError("Property 'type' is required")

    @classmethod
    def build(cls, *args, **kwargs):
        """Builds an instance of the appropriate subclass for the given ValueType."""

        init_dict = build_init_dict(args, kwargs)

        klass_map = {
            JSONType.NUMBER: NumberSchemaDict,
            JSONType.BOOLEAN: BooleanSchemaDict,
            JSONType.STRING: StringSchemaDict,
            JSONType.OBJECT: ObjectSchemaDict,
            JSONType.ARRAY: ArraySchemaDict
        }

        klass_type = init_dict.get("type")
        klass = klass_map.get(klass_type)

        if not klass:
            raise ValueError("Unknown type: {}".format(klass_type))

        return klass(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return {
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "const": self.const
        }

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return self._init.get("type")

    @property
    def required(self):
        """The required property tells whether this value is required to be specified."""

        return self._init.get("required", False)

    @property
    def description(self):
        """The description property represents a textual description of the value."""

        return self._init.get("description")

    @property
    def const(self):
        """The const property tells whether this value is constant."""

        return self._init.get("const")


class NumberSchemaDict(DataSchemaDict):
    """Properties to describe a numeric type."""

    def __init__(self, *args, **kwargs):
        super(NumberSchemaDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(NumberSchemaDict, self).to_dict()

        ret.update({
            "minimum": self.minimum,
            "maximum": self.maximum
        })

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.NUMBER

    @property
    def minimum(self):
        """The minimum property may be present when the value is of type
        number and if present, it defines the minimum value that can be used."""

        return self._init.get("minimum")

    @property
    def maximum(self):
        """The maximum property may be present when the value is of type
        number and if present, it defines the maximum value that can be used."""

        return self._init.get("maximum")


class BooleanSchemaDict(DataSchemaDict):
    """Properties to describe a boolean type."""

    def __init__(self, *args, **kwargs):
        super(BooleanSchemaDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(BooleanSchemaDict, self).to_dict()

        ret.update({})

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.BOOLEAN


class StringSchemaDict(DataSchemaDict):
    """Properties to describe a string type."""

    def __init__(self, *args, **kwargs):
        super(StringSchemaDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(StringSchemaDict, self).to_dict()

        ret.update({
            "enum": self.enum
        })

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.STRING

    @property
    def enum(self):
        """The enum property represents the list of allowed string values as a string array."""

        return self._init.get("enum", [])


class ObjectSchemaDict(DataSchemaDict):
    """Properties to describe an object type."""

    def __init__(self, *args, **kwargs):
        super(ObjectSchemaDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(ObjectSchemaDict, self).to_dict()

        ret.update({
            "properties": {
                key: val_type.to_dict()
                for key, val_type in six.iteritems(self.properties)
            },
            "required": self.required
        })

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.OBJECT

    @property
    def properties(self):
        """The properties property is a dictionary that contains the object properties."""

        return {
            key: DataSchemaDict.build(val)
            for key, val in six.iteritems(self._init.get("properties", {}))
        }

    @property
    def required(self):
        """The required property is a string array that containes the names
        that are mandatory to be present from the object properties."""

        return self._init.get("required", [])


class ArraySchemaDict(DataSchemaDict):
    """Properties to describe an array type."""

    def __init__(self, *args, **kwargs):
        super(ArraySchemaDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(ArraySchemaDict, self).to_dict()

        ret.update({
            "items": [val_type.to_dict() for val_type in self.items],
            "minItems": self.min_items,
            "maxItems": self.max_items
        })

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.ARRAY

    @property
    def items(self):
        """The items property is an array of ValueType elements."""

        return [DataSchemaDict.build(item) for item in self._init.get("items", [])]

    @property
    def min_items(self):
        """The minItems property represents the minimum
        number of elements required to be in the array."""

        return self._init.get("minItems", self._init.get("min_items"))

    @property
    def max_items(self):
        """The maxItems property represents the maximum
        number of elements that can be specified in the array."""

        return self._init.get("maxItems", self._init.get("max_items"))
