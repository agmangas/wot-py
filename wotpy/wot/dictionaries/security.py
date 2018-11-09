#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for security dictionaries defined in the Scripting API.
"""

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.wot.dictionaries.utils import build_init_dict
from wotpy.wot.enums import SecuritySchemeType


class SecuritySchemeDict(WotBaseDict):
    """Contains security related configuration."""

    class Meta:
        fields = {
            "scheme",
            "description",
            "proxy"
        }

        required = {
            "scheme"
        }

    @classmethod
    def build(cls, *args, **kwargs):
        """Builds an instance of the appropriate subclass for the given SecurityScheme."""

        init_dict = build_init_dict(args, kwargs)

        klass_map = {
            SecuritySchemeType.NOSEC: NoSecuritySchemeDict,
            SecuritySchemeType.BASIC: BasicSecuritySchemeDict
        }

        scheme_type = init_dict.get("scheme")
        klass = klass_map.get(scheme_type)

        if not klass:
            raise ValueError("Unknown scheme: {}".format(scheme_type))

        return klass(*args, **kwargs)


class NoSecuritySchemeDict(SecuritySchemeDict):
    """Indicates thate there is no authentication or
    other mechanism required to access the resource."""

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.NOSEC


class BasicSecuritySchemeDict(SecuritySchemeDict):
    """Properties that describe a basic security scheme."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "in",
            "name"
        })

        required = SecuritySchemeDict.Meta.required

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.BASIC
