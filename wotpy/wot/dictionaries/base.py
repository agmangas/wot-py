#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Base class for WoT dictionaries.
"""

import six

from wotpy.utils.utils import merge_args_kwargs_dict, to_camel, to_snake


class WotBaseDict(object):
    """Base class for all WoT data types represented
    as dictionaries in the Scripting API specification."""

    class Meta:
        fields = set()
        required = set()
        defaults = dict()

    def __init__(self, *args, **kwargs):
        """Constructor.
        Will raise ValueError if there is some required field missing."""

        init_dict = merge_args_kwargs_dict(args, kwargs)

        self._init = {}

        for key, val in six.iteritems(init_dict):
            self._init.update({to_camel(key): val})

        try:
            required = self.Meta.required
        except AttributeError:
            required = []

        for field in required:
            if field not in self._init:
                raise ValueError("Missing required field: {}".format(field))

    def __getattr__(self, name):
        """Transforms the field name to camelCase and
        attemps to retrieve it from the internal dict."""

        name_camel = to_camel(name)

        if name_camel not in self.Meta.fields:
            raise AttributeError(name)

        if name_camel in self._init:
            return self._init[name_camel]

        try:
            return self.Meta.defaults.get(name_camel, None)
        except AttributeError:
            return None

    def to_dict(self):
        """Returns the pure dict (JSON-serializable) representation of this WoT dictionary."""

        ret = {}

        def is_list_wot_dicts(x):
            return isinstance(x, list) and len(x) and hasattr(x[0], "to_dict")

        def is_dict_wot_dicts(x):
            return isinstance(x, dict) and len(x) and hasattr(next(six.itervalues(x)), "to_dict")

        def is_wot_dict(x):
            return hasattr(x, "to_dict")

        existing_fields = [
            f for f in self.Meta.fields
            if f in self._init or (to_snake(f) in dir(self) and getattr(self, to_snake(f)) is not None)
        ]

        for name_camel in existing_fields:
            field_val = getattr(self, to_snake(name_camel))

            if is_list_wot_dicts(field_val):
                field_val = [item.to_dict() for item in field_val]
            elif is_dict_wot_dicts(field_val):
                field_val = {key: val.to_dict() for key, val in six.iteritems(field_val)}
            elif is_wot_dict(field_val):
                field_val = field_val.to_dict()

            ret.update({name_camel: field_val})

        return ret
