#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ExposedThing(object):
    """An entity that serves to define the behavior of a Thing.
    An application uses this class when it acts as the Thing 'server'."""

    def __init__(self, servient, name):
        self.servient = servient
        self.name = name

    def invoke_action(self, action_name, *args):
        """Invokes an action."""

        pass

    def set_property(self, property_name, value):
        """Set a property value."""

        pass

    def get_property(self, property_name):
        """Get a property value."""

        pass

    def add_listener(self, event_name, listener):
        """Add a new listener for the given event."""

        pass

    def remove_listener(self, event_name, listener):
        """Removes an existing listener for the given event."""

        pass

    def remove_all_listeners(self, event_name):
        """Removes all listeners for the given event."""

        pass

    def get_description(self):
        """Get the thing description object."""

        pass

    def emit_event(self, event_name, payload):
        """Emit an event."""

        pass

    def add_event(self, event_name, payload_type, semantic_types=None):
        """Add an event that may be emitted by this Thing."""

        pass

    def add_action(self, action_name, input_type, output_type, semantic_types=None):
        """Add an action that may be invoked in this Thing."""

        pass

    def add_property(self, property_name, content_type, semantic_types=None):
        """Add a property."""

        pass

    def on_invoke_action(self, action_name, callback):
        """Callback to be called each time an action is invoked."""

        pass

    def on_update_property(self, property_name, callback):
        """Callback to be called each time a property is updated."""

        pass
