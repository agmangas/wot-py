#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities related to Futures and Promise-like objects.
"""

import tornado.concurrent


def is_future(obj):
    """Returns True if the given object looks like a Future."""

    if isinstance(obj, tornado.concurrent.Future):
        return True

    return hasattr(obj, "result") and \
           hasattr(obj, "add_done_callback") and \
           callable(obj.result) and \
           callable(obj.add_done_callback)
