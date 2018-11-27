#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Some utility functions for the WoT data type wrappers.
"""

import json

import six


def merge_args_kwargs_dict(args, kwargs):
    """Takes a tuple of args and dict of kwargs.
    Returns a dict that is the result of merging the first item
    of args (if that item is a dict) and the kwargs dict."""

    init_dict = {}

    if len(args) > 0 and isinstance(args[0], dict):
        init_dict = args[0]

    init_dict.update(kwargs)

    return init_dict


def to_camel(val):
    """Takes a string and transforms it to camelCase."""

    if not isinstance(val, six.string_types):
        raise ValueError

    parts = val.split("_")
    parts = parts[:1] + [item.title() for item in parts[1:]]

    return "".join(parts)


def to_snake(val):
    """Takes a string and transforms it to snake_case."""

    if not isinstance(val, six.string_types):
        raise ValueError

    return "".join(["_" + x.lower() if x.isupper() else x for x in val])


def to_json_obj(obj):
    """Recursive function that attempts to convert
    any given object to a JSON-serializable object."""

    if isinstance(obj, set):
        return list(obj)

    try:
        json.dumps(obj)
        return obj
    except TypeError:
        return {
            key: to_json_obj(val)
            for key, val in six.iteritems(vars(obj))
        }
