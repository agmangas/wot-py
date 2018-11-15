#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for versioning dictionaries defined in the Scripting API.
"""

from wotpy.wot.dictionaries.base import WotBaseDict


class VersioningDict(WotBaseDict):
    """Carries version information about the TD instance.
    If required, additional version information such as firmware and hardware version
    (term definitions outside of the TD namespace) can be extended here."""

    class Meta:
        fields = {
            "instance"
        }

        required = {
            "instance"
        }
