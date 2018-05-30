#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent Things exposed by a servient.
"""

# noinspection PyCompatibility
from concurrent.futures import Future
from rx import Observable
from rx.subjects import Subject

from wotpy.td.description import ThingDescription
from wotpy.td.interaction import Property, Action, Event
from wotpy.utils.enums import EnumListMixin
from wotpy.wot.dictionaries import \
    PropertyChangeEventInit, \
    ThingDescriptionChangeEventInit, \
    ActionInvocationEventInit
from wotpy.wot.enums import DefaultThingEvent, TDChangeMethod, TDChangeType
from wotpy.wot.events import \
    EmittedEvent, \
    PropertyChangeEmittedEvent, \
    ThingDescriptionChangeEmittedEvent, \
    ActionInvocationEmittedEvent
from wotpy.wot.interfaces.consumed import AbstractConsumedThing
from wotpy.wot.interfaces.exposed import AbstractExposedThing


class ExposedThingGroup(object):
    """Represents a group of ExposedThing objects.
    A group cannot contain two ExposedThing with the same Thing ID."""

    def __init__(self):
        self._exposed_things = {}

    @property
    def exposed_things(self):
        """A generator that yields all the ExposedThing contained in this group."""

        for exposed_thing in self._exposed_things.values():
            yield exposed_thing

    def contains(self, exposed_thing):
        """Returns True if this group contains the given ExposedThing."""

        return exposed_thing in self._exposed_things.values()

    def add(self, exposed_thing):
        """Add a new ExposedThing to this set."""

        if exposed_thing.thing.id in self._exposed_things:
            raise ValueError("Duplicate Exposed Thing: {}".format(exposed_thing.name))

        self._exposed_things[exposed_thing.thing.id] = exposed_thing

    def remove(self, name):
        """Removes an existing ExposedThing by name.
        The name argument may be the original name or the URL-safe version."""

        exposed_thing = self.find(name)

        if exposed_thing is None:
            raise ValueError("Unknown Exposed Thing: {}".format(name))

        assert exposed_thing.thing.id in self._exposed_things
        self._exposed_things.pop(exposed_thing.thing.id)

    def find(self, name):
        """Finds an existing ExposedThing by name.
        The name argument may be the original name or the URL-safe version."""

        def is_match(exp_thing):
            return exp_thing.name == name or exp_thing.url_name == name

        return next((item for item in self._exposed_things.values() if is_match(item)), None)

    def find_by_interaction(self, interaction):
        """Finds the ExposedThing whose Thing contains the given Interaction."""

        def is_match(exp_thing):
            return exp_thing.thing is interaction.thing

        return next((item for item in self._exposed_things.values() if is_match(item)), None)

    def find_by_thing(self, thing):
        """Finds the ExposedThing that is linked to the given Thing."""

        def is_match(exp_thing):
            return exp_thing.thing is thing

        return next((item for item in self._exposed_things.values() if is_match(item)), None)


class ExposedThing(AbstractConsumedThing, AbstractExposedThing):
    """An entity that serves to define the behavior of a Thing.
    An application uses this class when it acts as the Thing 'server'."""

    class HandlerKeys(EnumListMixin):
        """Enumeration of handler keys."""

        RETRIEVE_PROPERTY = "retrieve_property"
        UPDATE_PROPERTY = "update_property"
        INVOKE_ACTION = "invoke_action"
        OBSERVE = "observe"

    class InteractionStateKeys(EnumListMixin):
        """Enumeration of interaction state keys."""

        PROPERTY_VALUES = "property_values"

    def __init__(self, servient, thing):
        self._servient = servient
        self._thing = thing

        self._interaction_states = {
            self.InteractionStateKeys.PROPERTY_VALUES: {}
        }

        self._handlers_global = {
            self.HandlerKeys.RETRIEVE_PROPERTY: self._default_retrieve_property_handler,
            self.HandlerKeys.UPDATE_PROPERTY: self._default_update_property_handler,
            self.HandlerKeys.INVOKE_ACTION: self._default_invoke_action_handler
        }

        self._handlers = {
            self.HandlerKeys.RETRIEVE_PROPERTY: {},
            self.HandlerKeys.UPDATE_PROPERTY: {},
            self.HandlerKeys.INVOKE_ACTION: {}
        }

        self._events_stream = Subject()

    def __eq__(self, other):
        return self.servient == other.servient and self.thing == other.thing

    def __hash__(self):
        return hash((self.servient, self.thing))

    def _set_property_value(self, prop, value):
        """Sets a Property value."""

        prop_values = self.InteractionStateKeys.PROPERTY_VALUES
        self._interaction_states[prop_values][prop] = value

    def _get_property_value(self, prop):
        """Returns a Property value."""

        prop_values = self.InteractionStateKeys.PROPERTY_VALUES
        return self._interaction_states[prop_values].get(prop, None)

    def _set_handler(self, handler_type, handler, interaction=None):
        """Sets the currently defined handler for the given handler type."""

        if interaction is None or handler_type not in self._handlers:
            self._handlers_global[handler_type] = handler
        else:
            self._handlers[handler_type][interaction] = handler

    def _get_handler(self, handler_type, interaction=None):
        """Returns the currently defined handler for the given handler type."""

        interaction_handler = self._handlers.get(handler_type, {}).get(interaction, None)
        return interaction_handler or self._handlers_global[handler_type]

    def _find_interaction(self, name):
        """Raises ValueError if the given interaction does not exist in this Thing."""

        interaction = self._thing.find_interaction(name=name)

        if not interaction:
            raise ValueError("Interaction not found: {}".format(name))

        return interaction

    def _default_retrieve_property_handler(self, property_name):
        """Default handler for property reads."""

        future_read = Future()
        prop = self._find_interaction(name=property_name)
        prop_value = self._get_property_value(prop)
        future_read.set_result(prop_value)

        return future_read

    def _default_update_property_handler(self, property_name, value):
        """Default handler for onUpdateProperty."""

        future_write = Future()
        prop = self._find_interaction(name=property_name)
        self._set_property_value(prop, value)
        future_write.set_result(None)

        return future_write

    # noinspection PyMethodMayBeStatic
    def _default_invoke_action_handler(self):
        """Default handler for onInvokeAction."""

        future_invoke = Future()
        future_invoke.set_exception(Exception("Undefined action handler"))

        return future_invoke

    @property
    def servient(self):
        """Servient that contains this ExposedThing."""

        return self._servient

    @property
    def url_name(self):
        """Slug version (URL-safe) of the ExposedThing name."""

        return self._thing.url_name

    @property
    def name(self):
        """Name property."""

        return self._thing.name

    @property
    def thing(self):
        """Returns the object that represents the Thing beneath this ExposedThing."""

        return self._thing

    def get_thing_description(self):
        """Returns the Thing Description of the Thing.
        Returns a serialized string."""

        return self._thing.to_jsonld_str()

    def read_property(self, name):
        """Takes the Property name as the name argument, then requests from
        the underlying platform and the Protocol Bindings to retrieve the
        Property on the remote Thing and return the result. Returns a Future
        that resolves with the Property value or rejects with an Error."""

        try:
            interaction = self._find_interaction(name=name)

            handler = self._get_handler(
                handler_type=self.HandlerKeys.RETRIEVE_PROPERTY,
                interaction=interaction)

            future_read = handler(name)
        except Exception as ex:
            future_err = Future()
            future_err.set_exception(ex)
            return future_err

        return future_read

    def write_property(self, name, value):
        """Takes the Property name as the name argument and the new value as the
        value argument, then requests from the underlying platform and the Protocol
        Bindings to update the Property on the remote Thing and return the result.
        Returns a Future that resolves on success or rejects with an Error."""

        try:
            interaction = self._find_interaction(name=name)

            if not interaction.writable:
                raise TypeError("Property is non-writable")

            handler = self._get_handler(
                handler_type=self.HandlerKeys.UPDATE_PROPERTY,
                interaction=interaction)

            future_write = handler(name, value)
        except Exception as ex:
            future_err = Future()
            future_err.set_exception(ex)
            return future_err

        # noinspection PyUnusedLocal
        def publish_write_property_event(ft):
            event_init = PropertyChangeEventInit(name=name, value=value)
            self._events_stream.on_next(PropertyChangeEmittedEvent(init=event_init))

        if interaction.observable:
            future_write.add_done_callback(publish_write_property_event)

        return future_write

    def invoke_action(self, name, *args, **kwargs):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to
        invoke the Action on the remote Thing and return the result. Returns a
        Promise that resolves with the return value or rejects with an Error."""

        try:
            interaction = self._find_interaction(name=name)

            handler = self._get_handler(
                handler_type=self.HandlerKeys.INVOKE_ACTION,
                interaction=interaction)

            future_invoke = handler(*args, **kwargs)
        except Exception as ex:
            future_err = Future()
            future_err.set_exception(ex)
            return future_err

        # noinspection PyBroadException
        def publish_invoke_action_event(ft):
            try:
                result = ft.result()
            except Exception:
                return

            event_init = ActionInvocationEventInit(action_name=name, return_value=result)
            emitted_event = ActionInvocationEmittedEvent(init=event_init)
            self._events_stream.on_next(emitted_event)

        future_invoke.add_done_callback(publish_invoke_action_event)

        return future_invoke

    def on_event(self, name):
        """Returns an Observable for the Event specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        try:
            self._find_interaction(name=name)
        except ValueError:
            # noinspection PyUnresolvedReferences
            return Observable.throw(Exception("Unknown event"))

        def event_filter(item):
            return item.name == name

        # noinspection PyUnresolvedReferences
        return self._events_stream.filter(event_filter)

    def on_property_change(self, name):
        """Returns an Observable for the Property specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        try:
            interaction = self._find_interaction(name=name)
        except ValueError:
            # noinspection PyUnresolvedReferences
            return Observable.throw(Exception("Unknown property"))

        if not interaction.observable:
            # noinspection PyUnresolvedReferences
            return Observable.throw(Exception("Property is not observable"))

        def property_change_filter(item):
            return item.name == DefaultThingEvent.PROPERTY_CHANGE and \
                   item.data.name == name

        # noinspection PyUnresolvedReferences
        return self._events_stream.filter(property_change_filter)

    def on_td_change(self):
        """Returns an Observable, allowing subscribing to and unsubscribing
        from notifications to the Thing Description."""

        def td_change_filter(item):
            return item.name == DefaultThingEvent.DESCRIPTION_CHANGE

        # noinspection PyUnresolvedReferences
        return self._events_stream.filter(td_change_filter)

    def start(self):
        """Start serving external requests for the Thing."""

        self._servient.enable_exposed_thing(self.name)

    def stop(self):
        """Stop serving external requests for the Thing."""

        self._servient.disable_exposed_thing(self.name)

    def register(self, directory=None):
        """Generates the Thing Description given the properties, Actions
        and Event defined for this object. If a directory argument is given,
        make a request to register the Thing Description with the given WoT
        repository by invoking its register Action."""

        raise NotImplementedError()

    def unregister(self, directory=None):
        """If a directory argument is given, make a request to unregister
        the Thing Description with the given WoT repository by invoking its
        unregister Action. Then, and in the case no arguments were provided
        to this function, stop the Thing and remove the Thing Description."""

        raise NotImplementedError()

    def emit_event(self, event_name, payload):
        """Emits an the event initialized with the event name specified by
        the event_name argument and data specified by the payload argument."""

        if not self.thing.find_interaction(name=event_name):
            raise ValueError("Unknown event: {}".format(event_name))

        self._events_stream.on_next(EmittedEvent(name=event_name, init=payload))

    def add_property(self, property_init):
        """Adds a Property defined by the argument and updates the Thing Description.
        Takes an instance of ThingPropertyInit as argument."""

        prop = Property(
            thing=self._thing,
            id=property_init.name,
            type=property_init.type,
            writable=property_init.writable,
            observable=property_init.observable)

        self._thing.add_interaction(prop)
        self._set_property_value(prop, property_init.value)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.PROPERTY,
            method=TDChangeMethod.ADD,
            name=property_init.name,
            data=property_init,
            description=ThingDescription.from_thing(self.thing).to_dict())

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def remove_property(self, name):
        """Removes the Property specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name=name)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.PROPERTY,
            method=TDChangeMethod.REMOVE,
            name=name)

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def add_action(self, action_init):
        """Adds an Action to the Thing object as defined by the action
        argument of type ThingActionInit and updates th,e Thing Description."""

        action = Action(
            thing=self._thing,
            id=action_init.name,
            output=action_init.output_data_description,
            input=action_init.input_data_description)

        self._thing.add_interaction(action)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.ACTION,
            method=TDChangeMethod.ADD,
            name=action_init.name,
            data=action_init,
            description=ThingDescription.from_thing(self.thing).to_dict())

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def remove_action(self, name):
        """Removes the Action specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name=name)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.ACTION,
            method=TDChangeMethod.REMOVE,
            name=name)

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def add_event(self, event_init):
        """Adds an event to the Thing object as defined by the event argument
        of type ThingEventInit and updates the Thing Description."""

        event = Event(
            thing=self._thing,
            id=event_init.name,
            type=event_init.data_description)

        self._thing.add_interaction(event)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.EVENT,
            method=TDChangeMethod.ADD,
            name=event_init.name,
            data=event_init,
            description=ThingDescription.from_thing(self.thing).to_dict())

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def remove_event(self, name):
        """Removes the event specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name=name)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.EVENT,
            method=TDChangeMethod.REMOVE,
            name=name)

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def set_action_handler(self, action_handler, action_name=None):
        """Takes an action_name as an optional string argument, and an action handler.
        Sets the handler function for the specified Action matched by action_name if
        action_name is specified, otherwise sets it for any action. Throws on error."""

        interaction = None

        if action_name is not None:
            interaction = self._find_interaction(name=action_name)

        self._set_handler(
            handler_type=self.HandlerKeys.INVOKE_ACTION,
            handler=action_handler,
            interaction=interaction)

    def set_property_read_handler(self, read_handler, property_name=None):
        """Takes a property_name as an optional string argument, and a property read handler.
        Sets the handler function for reading the specified Property matched by property_name if
        property_name is specified, otherwise sets it for reading any property. Throws on error."""

        interaction = None

        if property_name is not None:
            interaction = self._find_interaction(name=property_name)

        self._set_handler(
            handler_type=self.HandlerKeys.RETRIEVE_PROPERTY,
            handler=read_handler,
            interaction=interaction)

    def set_property_write_handler(self, write_handler, property_name=None):
        """Takes a property_name as an optional string argument, and a property write handler.
        Sets the handler function for writing the specified Property matched by property_name if the
        property_name is specified, otherwise sets it for writing any properties. Throws on error."""

        interaction = None

        if property_name is not None:
            interaction = self._find_interaction(name=property_name)

        self._set_handler(
            handler_type=self.HandlerKeys.UPDATE_PROPERTY,
            handler=write_handler,
            interaction=interaction)
