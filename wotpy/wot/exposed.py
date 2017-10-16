#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rx import Observable

from wotpy.wot.dictionaries import ThingEventInit, ThingActionInit, ThingPropertyInit
from wotpy.wot.enums import RequestType
from wotpy.wot.interfaces.consumed import AbstractConsumedThing
from wotpy.wot.interfaces.exposed import AbstractExposedThing


class ExposedThing(AbstractConsumedThing, AbstractExposedThing):
    """An entity that serves to define the behavior of a Thing.
    An application uses this class when it acts as the Thing 'server'."""

    def __init__(self, servient, name, url, description):
        self._servient = servient
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

    def invoke_action(self, name, *args, **kwargs):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to
        invoke the Action on the remote Thing and return the result. Returns a
        Promise that resolves with the return value or rejects with an Error."""

        pass

    def remove_all_listeners(self, event_name=None):
        """Removes all listeners for the Event provided by
        the event_name optional argument, or if that was not
        provided, then removes all listeners from all Events."""

        pass

    def get_property(self, name):
        """Takes the Property name as the name argument, then requests from
        the underlying platform and the Protocol Bindings to retrieve the
        Property on  the remote Thing and return the result. Returns a Promise
        that resolves with the Property value or rejects with an Error."""

        pass

    def set_property(self, name, value):
        """Takes the Property name as the name argument and the new value as the
        value argument, then requests from the underlying platform and the Protocol
        Bindings to update the Property on the remote Thing and return the result.
        Returns a Promise that resolves on success or rejects with an Error."""

        pass

    def add_listener(self, event_name, listener):
        """Adds the listener provided in the argument listener to
        the Event name provided in the argument event_name."""

        pass

    def remove_listener(self, event_name, listener):
        """Removes a listener from the Event identified by
        the provided event_name and listener argument."""

        pass

    def observe(self, name, request_type):
        """Returns an Observable for the Property, Event or Action
        specified in the name argument, allowing subscribing and
        unsubscribing to notifications. The requestType specifies
        whether a Property, an Event or an Action is observed."""

        assert request_type in RequestType.list()
        # noinspection PyUnresolvedReferences
        return Observable.empty()

    def add_property(self, the_property):
        """Adds a Property defined by the argument and updates the Thing Description."""

        assert isinstance(the_property, ThingPropertyInit)

    def remove_property(self, name):
        """Removes the Property specified by the name argument,
        updates the Thing Description and returns the object."""

        pass

    def add_action(self, action):
        """Adds an Action to the Thing object as defined by the action
        argument of type ThingActionInit and updates the Thing Description."""

        assert isinstance(action, ThingActionInit)

    def remove_action(self, name):
        """Removes the Action specified by the name argument,
        updates the Thing Description and returns the object."""

        pass

    def add_event(self, event):
        """Adds an event to the Thing object as defined by the event argument
        of type ThingEventInit and updates the Thing Description."""

        assert isinstance(event, ThingEventInit)

    def remove_event(self, name):
        """Removes the event specified by the name argument,
        updates the Thing Description and returns the object."""

        pass

    def on_retrieve_property(self, handler):
        """Registers the handler function for Property retrieve requests received
        for the Thing, as defined by the handler property of type RequestHandler.
        The handler will receive an argument request of type Request where at least
        request.name is defined and represents the name of the Property to be retrieved."""

        pass

    def on_update_property(self, handler):
        """Defines the handler function for Property update requests received for the Thing,
        as defined by the handler property of type RequestHandler. The handler will receive
        an argument request of type Request where request.name defines the name of the
        Property to be retrieved and request.data defines the new value of the Property."""

        pass

    def on_invoke_action(self, handler):
        """Defines the handler function for Action invocation requests received
        for the Thing, as defined by the handler property of type RequestHandler.
        The handler will receive an argument request of type Request where request.name
        defines the name of the Action to be invoked and request.data defines the input
        arguments for the Action as defined by the Thing Description."""

        pass

    def on_observe(self, handler):
        """Defines the handler function for observe requests received for
        the Thing, as defined by the handler property of type RequestHandler.
        The handler will receive an argument request of type Request where:
        * request.name defines the name of the Property or Action or event to be observed.
        * request.options.observeType is of type RequestType and defines whether a
        Property change or Action invocation or event emitting is observed, or the
        changes to the Thing Description are observed.
        * request.options.subscribe is true if subscription is turned or kept being
        turned on, and it is false when subscription is turned off."""

        pass

    def register(self, directory=None):
        """Generates the Thing Description given the properties, Actions
        and Event defined for this object. If a directory argument is given,
        make a request to register the Thing Description with the given WoT
        repository by invoking its register Action."""

        pass

    def unregister(self, directory=None):
        """If a directory argument is given, make a request to unregister
        the Thing Description with the given WoT repository by invoking its
        unregister Action. Then, and in the case no arguments were provided
        to this function, stop the Thing and remove the Thing Description."""

        pass

    def start(self):
        """Start serving external requests for the Thing."""

        pass

    def stop(self):
        """Stop serving external requests for the Thing."""

        pass

    def emit_event(self, event_name, payload):
        """Emits an the event initialized with the event name specified by
        the event_name argument and data specified by the payload argument."""

        pass
