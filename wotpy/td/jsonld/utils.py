#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utilities related to objects in the TD hierarchy serialized in JSON-LD.
"""

from wotpy.td.enums import InteractionTypes


def get_interaction_type(doc):
    """Returns the type (event, property or action)
    of the given interaction JSON-LD document."""

    for item in doc.get("@type", []):
        if item in InteractionTypes.list():
            return item

    raise ValueError("Unknown interaction type")
