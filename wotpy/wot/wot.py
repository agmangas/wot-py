#!/usr/bin/env python
# -*- coding: utf-8 -*-


class WoT(object):
    """WoT entrypoint."""

    def __init__(self, servient):
        self.servient = servient

    def discover(self, discovery_type, filter_obj):
        """Discover a Thing."""

        pass

    def consume_description_uri(self, uri):
        """Recover a ConsumedThing by consuming its thing description URI."""

        pass

    def consume_description(self, thing_description):
        """Recover a ConsumedThing by consuming its thing description object."""

        pass

    def create_thing(self, name):
        """Create a Thing in the current context from a name."""

        pass

    def create_from_description_uri(self, uri):
        """Create a Thing in the current context from a thing description URI."""

        pass

    def create_from_description(self, thing_description):
        """Create a Thing in the current context from a thing description object."""

        pass
