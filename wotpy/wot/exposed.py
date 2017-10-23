#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyCompatibility
from concurrent.futures import Future

from rx import Observable

from wotpy.td.enums import InteractionTypes
from wotpy.td.interaction import Property, Action, Event
from wotpy.td.thing import Thing
from wotpy.wot.enums import RequestType
from wotpy.wot.interfaces.consumed import AbstractConsumedThing
from wotpy.wot.interfaces.exposed import AbstractExposedThing


class ExposedThing(AbstractConsumedThing, AbstractExposedThing):
    """An entity that serves to define the behavior of a Thing.
    An application uses this class when it acts as the Thing 'server'."""

    def __init__(self, servient, thing):
        self._servient = servient
        self._thing = thing
        self._prop_values = {}
        self._action_funcs = {}

    @classmethod
    def from_name(cls, servient, name):
        """Builds an empty ExposedThing with the given name."""

        thing = Thing(name=name)
        return ExposedThing(servient=servient, thing=thing)

    @classmethod
    def from_url(cls, servient, url):
        """Builds an ExposedThing initialized from the data
        retrieved from the Thing Description document at the URL."""

        raise NotImplementedError()

    @classmethod
    def from_description(cls, servient, doc):
        """Builds an ExposedThing initialized from
        the given Thing Description document."""

        raise NotImplementedError()

    def _set_property_value(self, prop, value):
        """Sets a Property value."""

        self._prop_values[prop] = value

    def _get_property_value(self, prop):
        """Returns a Property value."""

        return self._prop_values.get(prop, None)

    def _set_action_func(self, action, func):
        """Sets the action function of an Action."""

        self._action_funcs[action] = func

    def _get_action_func(self, action):
        """Returns the action function of an Action."""

        return self._action_funcs.get(action, None)

    @property
    def name(self):
        """Name property."""

        return self._thing.name

    @property
    def url(self):
        """URL property."""

        return None

    @property
    def description(self):
        """Description property."""

        return self._thing.to_jsonld_thing_description().doc

    def get_property(self, name):
        """Takes the Property name as the name argument, then requests from
        the underlying platform and the Protocol Bindings to retrieve the
        Property on the remote Thing and return the result. Returns a Promise
        that resolves with the Property value or rejects with an Error."""

        proprty = self._thing.find_interaction(
            name, interaction_type=InteractionTypes.PROPERTY)

        future = Future()

        if proprty:
            value = self._get_property_value(proprty)
            future.set_result(value)
        else:
            future.set_exception(ValueError())

        return future

    def set_property(self, name, value):
        """Takes the Property name as the name argument and the new value as the
        value argument, then requests from the underlying platform and the Protocol
        Bindings to update the Property on the remote Thing and return the result.
        Returns a Promise that resolves on success or rejects with an Error."""

        proprty = self._thing.find_interaction(
            name, interaction_type=InteractionTypes.PROPERTY)

        future = Future()

        if proprty:
            self._set_property_value(proprty, value)
            future.set_result(True)
        else:
            future.set_exception(ValueError())

        return future

    def invoke_action(self, name, *args, **kwargs):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to
        invoke the Action on the remote Thing and return the result. Returns a
        Promise that resolves with the return value or rejects with an Error."""

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

    def add_property(self, property_init):
        """Adds a Property defined by the argument and updates the Thing Description.
        Takes an instance of ThingPropertyInit as argument."""

        prop = Property(
            thing=self._thing,
            name=property_init.name,
            output_data=property_init.description,
            writable=property_init.writable)

        for item in property_init.semantic_types:
            self._thing.add_context(context_url=item.context)
            prop.add_type(item.name)

        self._thing.add_interaction(prop)
        self._set_property_value(prop, property_init.value)

    def remove_property(self, name):
        """Removes the Property specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name, interaction_type=InteractionTypes.PROPERTY)

    def add_action(self, action_init):
        """Adds an Action to the Thing object as defined by the action
        argument of type ThingActionInit and updates th,e Thing Description."""

        action = Action(
            thing=self._thing,
            name=action_init.name,
            output_data=action_init.output_data_description,
            input_data=action_init.input_data_description)

        for item in action_init.semantic_types:
            self._thing.add_context(context_url=item.context)
            action.add_type(item.name)

        self._thing.add_interaction(action)
        self._set_action_func(action, action_init.action)

    def remove_action(self, name):
        """Removes the Action specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name, interaction_type=InteractionTypes.ACTION)

    def add_event(self, event_init):
        """Adds an event to the Thing object as defined by the event argument
        of type ThingEventInit and updates the Thing Description."""

        event = Event(
            thing=self._thing,
            name=event_init.name,
            output_data=event_init.data_description)

        for item in event_init.semantic_types:
            self._thing.add_context(context_url=item.context)
            event.add_type(item.name)

        self._thing.add_interaction(event)

    def remove_event(self, name):
        """Removes the event specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name, interaction_type=InteractionTypes.EVENT)

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
