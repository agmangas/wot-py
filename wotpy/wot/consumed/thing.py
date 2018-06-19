#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents a Thing consumed by a servient.
"""

import tornado.gen

from wotpy.wot.interfaces.consumed import AbstractConsumedThing


class ConsumedThing(AbstractConsumedThing):
    """An entity that serves to interact with a Thing.
    An application uses this class when it acts as a *client* of the Thing."""

    def __init__(self, servient, td):
        self.servient = servient
        self.td = td

    @property
    def name(self):
        """User-given name of the Thing."""

        return self.td.name

    def get_thing_description(self):
        """Returns the Thing Description of the Thing.
        Returns a serialized string."""

        return self.td.to_str()

    @tornado.gen.coroutine
    def invoke_action(self, name, input_value=None):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to invoke
        the Action on the remote Thing and return the result.
        Returns a Future that resolves with the return value or rejects with an Error."""

        client = self.servient.select_client(self.td, name)
        result = yield client.invoke_action(self.td, name, input_value)

        raise tornado.gen.Return(result)

    @tornado.gen.coroutine
    def write_property(self, name, value):
        """Takes the Property name as the name argument and the new value as the value
        argument, then requests from the underlying platform and the Protocol Bindings
        to update the Property on the remote Thing and return the result.
        Returns a Future that resolves on success or rejects with an Error."""

        client = self.servient.select_client(self.td, name)
        yield client.write_property(self.td, name, value)

    @tornado.gen.coroutine
    def read_property(self, name):
        """Takes the Property name as the name argument, then requests from the
        underlying platform and the Protocol Bindings to retrieve the Property
        on the remote Thing and return the result.
        Returns a Future that resolves with the Property value or rejects with an Error."""

        client = self.servient.select_client(self.td, name)
        value = yield client.read_property(self.td, name)

        raise tornado.gen.Return(value)

    def on_event(self, name):
        """Returns an Observable for the Event specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        client = self.servient.select_client(self.td, name)
        return client.on_event(self.td, name)

    def on_property_change(self, name):
        """Returns an Observable for the Property specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        client = self.servient.select_client(self.td, name)
        return client.on_property_change(self.td, name)

    def on_td_change(self):
        """Returns an Observable, allowing subscribing to and unsubscribing
        from notifications to the Thing Description."""

        raise NotImplementedError()

    @property
    def properties(self):
        """Represents a dictionary of ThingProperty items."""

        raise NotImplementedError()

    @property
    def actions(self):
        """Represents a dictionary of ThingAction items."""

        raise NotImplementedError()

    @property
    def events(self):
        """Represents a dictionary of ThingEvent items."""

        raise NotImplementedError()

    @property
    def links(self):
        """Represents a dictionary of WebLink items."""

        raise NotImplementedError()

    def subscribe(self):
        """Subscribes to changes on the TD of this thing."""

        raise NotImplementedError()
