#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper class for dictionaries to represent Thing filters.
"""

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.wot.enums import DiscoveryMethod


class ThingFilterDict(WotBaseDict):
    """The ThingFilter dictionary that represents the
    constraints for discovering Things as key-value pairs."""

    class Meta:
        fields = {
            "method",
            "url",
            "query",
            "fragment"
        }

        defaults = {
            "method": DiscoveryMethod.ANY
        }
