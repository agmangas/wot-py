#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

from wotpy.td.interaction import Interaction


class ThingDescription(object):
    """A ThingDescription JSON-LD document."""

    @classmethod
    def loads(cls, json_str):
        """Build a ThingDescription instance from
        a JSON document serialized as string."""

        return ThingDescription(json.loads(json_str))

    def __init__(self, doc):
        self._doc = doc

    @property
    def name(self):
        """Name getter."""

        return self._doc.get('name')

    @property
    def base(self):
        """Base getter."""

        return self._doc.get('base')

    @property
    def type(self):
        """Type getter."""

        return self._doc.get('@type')

    @property
    def context(self):
        """Context getter."""

        return self._doc.get('@context')

    @property
    def interaction(self):
        """Returns a list of Interaction instances that represent
        the interactions contained in this Thing Description."""

        return [Interaction(item) for item in self._doc.get('interaction', [])]
