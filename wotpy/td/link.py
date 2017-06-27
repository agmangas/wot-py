#!/usr/bin/env python
# -*- coding: utf-8 -*-


class InteractionLink(object):
    """A link JSON-LD document."""

    def __init__(self, doc):
        self._doc = doc

    @property
    def href(self):
        """Href getter."""

        return self._doc.get('href')

    @property
    def media_type(self):
        """Media type getter."""

        return self._doc.get('mediaType')
