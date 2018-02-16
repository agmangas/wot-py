#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.wot.interfaces.consumed import AbstractConsumedThing


class ConsumedThing(AbstractConsumedThing):
    """An entity that serves to interact with a Thing.
    An application uses this class when it acts as a 'client' of the Thing."""

    def __init__(self, servient, jsonld_td):
        self.servient = servient
        self._jsonld_td = jsonld_td

    @property
    def name(self):
        """User-given name of the Thing."""

        return self._jsonld_td.name

    @property
    def jsonld_td(self):
        """Returns the object that wraps the JSON-LD
        serialization of the TD that describes this Thing."""

        return self._jsonld_td

    def get_thing_description(self):
        """Returns the Thing Description of the Thing.
        Returns a serialized string."""

        raise NotImplementedError()

    def invoke_action(self, name, *args):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to invoke
        the Action on the remote Thing and return the result.
        Returns a Future that resolves with the return value or rejects with an Error."""

        raise NotImplementedError()

    def write_property(self, name, value):
        """Takes the Property name as the name argument and the new value as the value
        argument, then requests from the underlying platform and the Protocol Bindings
        to update the Property on the remote Thing and return the result.
        Returns a Future that resolves on success or rejects with an Error."""

        raise NotImplementedError()

    def read_property(self, name):
        """Takes the Property name as the name argument, then requests from the
        underlying platform and the Protocol Bindings to retrieve the Property
        on the remote Thing and return the result.
        Returns a Future that resolves with the Property value or rejects with an Error."""

        raise NotImplementedError()

    def on_event(self, name):
        """Returns an Observable for the Event specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        raise NotImplementedError()

    def on_property_change(self, name):
        """Returns an Observable for the Property specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        raise NotImplementedError()

    def on_td_change(self):
        """Returns an Observable, allowing subscribing to and unsubscribing
        from notifications to the Thing Description."""

        raise NotImplementedError()
