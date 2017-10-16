#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyCompatibility
from concurrent.futures import Future

from wotpy.resources.listeners.base import BaseResourceListener


class PropertyResourceListener(BaseResourceListener):
    """Resource listener for properties."""

    def __init__(self, exposed_thing, interaction):
        self.exposed_thing = exposed_thing
        self.interaction = interaction

    @property
    def _property_name(self):
        """Getter for the name of this property interaction."""

        return self.exposed_thing.name

    def on_read(self):
        """Called to handle property reads.
        Returns a future that resolves to the property value."""

        property_value = self.exposed_thing.get_property(self._property_name)

        future = Future()
        future.set_result(property_value)

        return future

    def on_write(self, value):
        """Called to handle property writes.
        Returns a future that resolves to void when the write is finished."""

        self.exposed_thing.set_property(self._property_name, value)

        future = Future()
        future.set_result(True)

        return future
