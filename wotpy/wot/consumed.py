#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rx import Observable

from wotpy.wot.enums import RequestType
from wotpy.wot.interfaces.consumed import AbstractConsumedThing


class ConsumedThing(AbstractConsumedThing):
    """An entity that serves to interact with a Thing.
    An application uses this class when it acts as a 'client' of the Thing."""

    def __init__(self, servient, name, url, description):
        self.servient = servient
        self._name = name
        self._url = url
        self._description = description

    @property
    def name(self):
        """Name property."""

        return self._name

    @property
    def url(self):
        """URL property."""

        return self._url

    @property
    def description(self):
        """Description property."""

        return self._description

    def invoke_action(self, name, *args):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to
        invoke the Action on the remote Thing and return the result. Returns a
        Promise that resolves with the return value or rejects with an Error."""

        pass

    def set_property(self, name, value):
        """Takes the Property name as the name argument and the new value as the
        value argument, then requests from the underlying platform and the Protocol
        Bindings to update the Property on the remote Thing and return the result.
        Returns a Promise that resolves on success or rejects with an Error."""

        pass

    def get_property(self, name):
        """Takes the Property name as the name argument, then requests from
        the underlying platform and the Protocol Bindings to retrieve the
        Property on  the remote Thing and return the result. Returns a Promise
        that resolves with the Property value or rejects with an Error."""

        pass

    def add_listener(self, event_name, listener):
        """Adds the listener provided in the argument listener to
        the Event name provided in the argument event_name."""

        pass

    def remove_listener(self, event_name, listener):
        """Removes a listener from the Event identified by
        the provided event_name and listener argument."""

        pass

    def remove_all_listeners(self, event_name=None):
        """Removes all listeners for the Event provided by
        the event_name optional argument, or if that was not
        provided, then removes all listeners from all Events."""

        pass

    def observe(self, name, request_type):
        """Returns an Observable for the Property, Event or Action
        specified in the name argument, allowing subscribing and
        unsubscribing to notifications. The requestType specifies
        whether a Property, an Event or an Action is observed."""

        assert request_type in RequestType.list()
        # noinspection PyUnresolvedReferences
        return Observable.empty()
