#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Some utility functions for the WoT data type wrappers.
"""

import six


def build_init_dict(args, kwargs):
    """Takes a tuple of args and dict of kwargs and updates the kwargs dict
    with the first argument of args (if that item is a dict)."""

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
