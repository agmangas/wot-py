#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.resources.listeners.base import BaseResourceListener
from wotpy.wot.enums import RequestType


class PropertyResourceListener(BaseResourceListener):
    """Resource listener for properties."""

    def __init__(self, exposed_thing, interaction):
        self._exposed_thing = exposed_thing
        self._interaction = interaction

    def on_read(self):
        """Called to handle property reads.
        Returns a future that resolves to the property value."""

        return self._exposed_thing.get_property(self._interaction.name)

    def on_write(self, value):
        """Called to handle property writes.
        Returns a future that resolves to void when the write is finished."""

        return self._exposed_thing.set_property(self._interaction.name, value)

    def on_observe(self):
        """Called to handle resource observations.
        Returns an Observable."""

        return self._exposed_thing.observe(self._interaction.name, RequestType.PROPERTY)


class ActionResourceListener(BaseResourceListener):
    """Resource listener for actions."""

    def __init__(self, exposed_thing, interaction):
        self._exposed_thing = exposed_thing
        self._interaction = interaction

    def on_invoke(self, **kwargs):
        """Called to handle resource invocations.
        Returns a future that resolves to the invocation response."""

        return self._exposed_thing.invoke_action(self._interaction.name, **kwargs)

    def on_observe(self):
        """Called to handle resource observations.
        Returns an Observable."""

        return self._exposed_thing.observe(self._interaction.name, RequestType.ACTION)


class EventResourceListener(BaseResourceListener):
    """Resource listener for events."""

    def __init__(self, exposed_thing, interaction):
        self._exposed_thing = exposed_thing
        self._interaction = interaction

    def on_observe(self):
        """Called to handle resource observations.
        Returns an Observable."""

        return self._exposed_thing.observe(self._interaction.name, RequestType.EVENT)
