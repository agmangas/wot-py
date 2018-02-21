#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities related to strings.
"""

import re


def is_safe_name(val):
    """Returns True if the given value is a safe name for an object
    in the Thing hierarchy.  A name is considered safe when it only
    contains ASCII letters, numbers, hyphens and underscores."""

    pattern_safe = r"^[a-zA-Z0-9_-]+$"
    match_result = re.match(pattern_safe, val)

    return False if match_result is None else True
