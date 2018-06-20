#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for security dictionaries defined in the Scripting API.
"""

from wotpy.wot.dictionaries.utils import build_init_dict


class SecuritySchemeDict(object):
    """Contains security related configuration."""

    def __init__(self, *args, **kwargs):
        self._init = build_init_dict(args, kwargs)

        if self.scheme is None:
            raise ValueError("Property 'scheme' is required")

    @classmethod
    def build(cls, *args, **kwargs):
        """Builds an instance of the appropriate subclass for the given SecurityScheme."""

        raise NotImplementedError()

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return self._init

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return self._init.get("scheme")

    @property
    def in_data(self):
        """The in property represents security initialization data
        as described in the Security metadata description document."""

        return self._init.get("in")
