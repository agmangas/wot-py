#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.td.link import InteractionLink


class InteractionTypes(object):
    """Enumeration of interaction types."""

    PROPERTY = 'Property'
    ACTION = 'Action'
    EVENT = 'Event'

    @classmethod
    def list(cls):
        """Returns a list with all interaction types."""

        return [cls.PROPERTY, cls.ACTION, cls.EVENT]


class Interaction(object):
    """An interaction sub-document contained within
    a Thing Description JSON-LD document."""

    def __init__(self, doc):
        self._doc = doc

    @property
    def interaction_type(self):
        """Returns the interaction type."""

        for item in self.type:
            if item in InteractionTypes.list():
                return item

    @property
    def type(self):
        """Type getter."""

        return self._doc.get('@type')

    @property
    def name(self):
        """Name getter."""

        return self._doc.get('name')

    @property
    def output_data(self):
        """outputData getter."""

        return self._doc.get('outputData')

    @property
    def input_data(self):
        """inputData getter."""

        return self._doc.get('inputData')

    @property
    def writable(self):
        """Writable getter."""

        return self._doc.get('writable')

    @property
    def stability(self):
        """Stability getter."""

        return self._doc.get('stability')

    @property
    def link(self):
        """Returns a list of InteractionLink instances that
        represent the links contained in this interaction."""

        return [InteractionLink(item) for item in self._doc.get('link', [])]
