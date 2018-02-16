#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import six


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
            for key, val in six.iteritems(obj.__dict__)
        }
