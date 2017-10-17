#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings
import string


def clean_str(val, warn=False):
    """Returns a copy of the str argument keeping only
    ASCII letters, numbers, hyphens and underscores."""

    valid_chars = set(string.ascii_letters + string.digits + "_-")
    val_clean = "".join(item for item in val if item in valid_chars)

    if warn and val_clean != val:
        warnings.warn("Unsafe str \"{}\" (using: \"{}\")".format(val, val_clean))

    return val_clean
