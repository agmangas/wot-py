#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for data schema dictionaries defined in the Scripting API.
"""

import six

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.wot.dictionaries.utils import build_init_dict
from wotpy.wot.enums import DataType


class DataSchema(WotBaseDict):
    """Represents the common properties of a value type definition."""

    class Meta:
        fields = {
            "description",
            "title",
            "type",
            "const",
            "unit",
            "enum",
            "readOnly",
            "writeOnly"
        }

        defaults = {
            "readOnly": False,
            "writeOnly": False
        }

    @classmethod
    def build(cls, *args, **kwargs):
        """Builds an instance of the appropriate subclass for the given ValueType."""

        init_dict = build_init_dict(args, kwargs)

        klass_map = {
            DataType.NUMBER: NumberSchema,
            DataType.BOOLEAN: BooleanSchema,
            DataType.STRING: StringSchema,
            DataType.OBJECT: ObjectSchema,
            DataType.ARRAY: ArraySchema,
            DataType.INTEGER: IntegerSchema
        }

        klass_type = init_dict.get("type")
        klass = klass_map.get(klass_type)

        if not klass:
            raise ValueError("Unknown type: {}".format(klass_type))

        return klass(*args, **kwargs)


class NumberSchema(DataSchema):
    """Properties to describe a numeric type."""

    class Meta:
        fields = DataSchema.Meta.fields.union({
            "minimum",
            "maximum"
        })

        defaults = DataSchema.Meta.defaults

    @property
    def type(self):
        """The type property represents the value type (a member of DataType)."""

        return DataType.NUMBER


class BooleanSchema(DataSchema):
    """Properties to describe a boolean type."""

    @property
    def type(self):
        """The type property represents the value type enumerated in DataType."""

        return DataType.BOOLEAN


class StringSchema(DataSchema):
    """Properties to describe a string type."""

    @property
    def type(self):
        """The type property represents the value type enumerated in DataType."""

        return DataType.STRING


class ObjectSchema(DataSchema):
    """Properties to describe an object type."""

    class Meta:
        fields = DataSchema.Meta.fields.union({
            "properties",
            "required"
        })

        defaults = DataSchema.Meta.defaults

    @property
    def type(self):
        """The type property represents the value type enumerated in DataType."""

        return DataType.OBJECT

    @property
    def properties(self):
        """Data schema nested definitions."""

        return {
            key: DataSchema.build(val)
            for key, val in six.iteritems(self._init.get("properties", {}))
        }


class ArraySchema(DataSchema):
    """Properties to describe an array type."""

    class Meta:
        fields = DataSchema.Meta.fields.union({
            "items",
            "minItems",
            "maxItems"
        })

        defaults = DataSchema.Meta.defaults

    @property
    def type(self):
        """The type property represents the value type enumerated in DataType."""

        return DataType.ARRAY

    @property
    def items(self):
        """Used to define the characteristics of an array."""

        return DataSchema.build(self._init["items"]) if "items" in self._init else None


class IntegerSchema(NumberSchema):
    """Properties to describe an integer type."""

    @property
    def type(self):
        """The type property represents the value type enumerated in DataType."""

        return DataType.INTEGER
