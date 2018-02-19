#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities related to enumerations.
"""

import six


class EnumListMixin(object):
    """Mixin that provides methods to list enumerated values."""

    @classmethod
    def list(cls):
        """Returns a list of enumerated values."""

        def _is_enumerate_item(attr_name, attr_val):
            return not attr_name.startswith("__") \
                   and isinstance(attr_val, six.string_types) \
                   and attr_name.isupper()

        return [
            val for (name, val) in cls.__dict__.items()
            if _is_enumerate_item(name, val)]
