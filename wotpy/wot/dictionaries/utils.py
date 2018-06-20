#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Some utility functions for the WoT data type wrappers.
"""


def build_init_dict(args, kwargs):
    """Takes a tuple of args and dict of kwargs and updates the kwargs dict
    with the first argument of args (if that item is a dict)."""

    init_dict = {}

    if len(args) > 0 and isinstance(args[0], dict):
        init_dict = args[0]

    init_dict.update(kwargs)

    return init_dict
