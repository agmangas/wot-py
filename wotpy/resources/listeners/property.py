#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.resources.listeners.base import BaseResourceListener


class PropertyResourceListener(BaseResourceListener):
    """Resource listener for properties."""

    def __init__(self, exposed_thing, interaction):
        self.exposed_thing = exposed_thing
        self.interaction = interaction

    def on_read(self):
        """Called to handle property reads.
        Returns a future that resolves to the property value."""

        pass

    def on_write(self, value):
        """Called to handle property writes.
        Returns a future that resolves to void when the write is finished."""

        pass
