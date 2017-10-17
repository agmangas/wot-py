#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string


def clean_str(val):
    """Returns a copy of the str argument keeping only
    ASCII letters, numbers, hyphens and underscores."""

    valid_chars = set(string.ascii_letters + string.digits + "_-")
    return "".join(item for item in val if item in valid_chars)
