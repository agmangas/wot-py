#!/usr/bin/env python
# -*- coding: utf-8 -*-


class ConsumedThing(object):
    """An entity that serves to interact with a Thing.
    An application uses this class when it acts as a 'client' of the Thing."""

    def __init__(self, servient, thing_description):
        self.servient = servient
        self.thing_description = thing_description

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
