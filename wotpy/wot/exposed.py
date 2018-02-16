#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import six
# noinspection PyCompatibility
from concurrent.futures import Future, ThreadPoolExecutor
from rx import Observable
from rx.subjects import Subject
from tornado.httpclient import HTTPClient, HTTPRequest

from wotpy.td.enums import InteractionTypes
from wotpy.td.interaction import Property, Action, Event
from wotpy.td.jsonld.thing import JsonLDThingDescription
from wotpy.td.thing import Thing
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

    @classmethod
    def from_name(cls, servient, name):
        """Builds an empty ExposedThing with the given name."""

        thing = Thing(name=name)

        return ExposedThing(servient=servient, thing=thing)

    @classmethod
    def from_url(cls, servient, url, name=None, timeout_secs=10.0):
        """Builds an ExposedThing initialized from the data
        retrieved from the Thing Description document at the URL.
        Returns a Future that resolves to the ExposedThing."""

        future_thing = Future()

        def fetch_td():
            http_client = HTTPClient()
            http_request = HTTPRequest(url, request_timeout=timeout_secs)
            http_response = http_client.fetch(http_request)
            td_doc = json.loads(http_response.body)
            http_client.close()
            return td_doc

        def build_exposed_thing(ft):
            try:
                td_doc = ft.result()
                exp_thing = cls.from_description(servient=servient, doc=td_doc, name=name)
                future_thing.set_result(exp_thing)
            except Exception as ex:
                future_thing.set_exception(ex)

        executor = ThreadPoolExecutor(max_workers=1)
        future_td = executor.submit(fetch_td)
        future_td.add_done_callback(build_exposed_thing)
        executor.shutdown(wait=False)

        return future_thing

    @classmethod
    def from_description(cls, servient, doc, name=None):
        """Builds an ExposedThing initialized from
        the given Thing Description document."""

        jsonld_td = JsonLDThingDescription(doc=doc)

        name = name or jsonld_td.name
        thing = Thing(name=name)

        for context_item in (jsonld_td.context or []):
            if isinstance(context_item, six.string_types):
                thing.semantic_context.add(context_url=context_item)
            elif isinstance(context_item, dict):
                for ctx_key, ctx_val in six.iteritems(context_item):
                    thing.semantic_context.add(context_url=ctx_val, prefix=ctx_key)

        for val_type in (jsonld_td.type or []):
            thing.semantic_types.add(val_type)

        for meta_key, meta_val in six.iteritems(jsonld_td.metadata):
            thing.semantic_metadata.add(meta_key, meta_val)

        def _build_property(jsonld_inter):
            return Property(
                thing=thing,
                name=jsonld_inter.name,
                output_data=jsonld_inter.output_data,
                writable=jsonld_inter.writable,
                observable=jsonld_inter.observable)

        def _build_action(jsonld_inter):
            return Action(
                thing=thing,
                name=jsonld_inter.name,
                output_data=jsonld_inter.output_data,
                input_data=jsonld_inter.input_data)

        def _build_event(jsonld_inter):
            return Event(
                thing=thing,
                name=jsonld_inter.name,
                output_data=jsonld_inter.output_data)

        builder_map = {
            InteractionTypes.PROPERTY: _build_property,
            InteractionTypes.ACTION: _build_action,
            InteractionTypes.EVENT: _build_event
        }

        for jsonld_interaction in jsonld_td.interaction:
            builder_func = builder_map[jsonld_interaction.interaction_type]
            interaction = builder_func(jsonld_interaction)

            for val_type in (jsonld_interaction.type or []):
                interaction.semantic_types.add(val_type)

            for meta_key, meta_val in six.iteritems(jsonld_interaction.metadata):
                interaction.semantic_metadata.add(meta_key, meta_val)

            thing.add_interaction(interaction)

        return ExposedThing(servient=servient, thing=thing)

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

    def _find_interaction(self, interaction_name, interaction_type):
        """Raises ValueError if the given interaction does not exist in this Thing."""

        interaction = self._thing.find_interaction(
            name=interaction_name,
            interaction_type=interaction_type)

        if not interaction:
            raise ValueError("Interaction ({}) not found: {}".format(
                interaction_type, interaction_name))

        return interaction

    def _default_retrieve_property_handler(self, property_name):
        """Default handler for property reads."""

        future_read = Future()

        prop = self._find_interaction(
            interaction_name=property_name,
            interaction_type=InteractionTypes.PROPERTY)

        prop_value = self._get_property_value(prop)

        future_read.set_result(prop_value)

        return future_read

    def _default_update_property_handler(self, property_name, value):
        """Default handler for onUpdateProperty."""

        future_write = Future()

        prop = self._find_interaction(
            interaction_name=property_name,
            interaction_type=InteractionTypes.PROPERTY)

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

        return self._thing.to_jsonld_thing_description().to_json_str()

    def read_property(self, name):
        """Takes the Property name as the name argument, then requests from
        the underlying platform and the Protocol Bindings to retrieve the
        Property on the remote Thing and return the result. Returns a Future
        that resolves with the Property value or rejects with an Error."""

        try:
            interaction = self._find_interaction(
                interaction_name=name,
                interaction_type=InteractionTypes.PROPERTY)

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
            interaction = self._find_interaction(
                interaction_name=name,
                interaction_type=InteractionTypes.PROPERTY)

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
            event_data = PropertyChangeEventInit(name=name, value=value)
            self._events_stream.on_next(PropertyChangeEmittedEvent(init=event_data))

        future_write.add_done_callback(publish_write_property_event)

        return future_write

    def invoke_action(self, name, *args, **kwargs):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to
        invoke the Action on the remote Thing and return the result. Returns a
        Promise that resolves with the return value or rejects with an Error."""

        try:
            interaction = self._find_interaction(
                interaction_name=name,
                interaction_type=InteractionTypes.ACTION)

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
                return_value = ft.result()
                event_data = ActionInvocationEventInit(action_name=name, return_value=return_value)
                emitted_event = ActionInvocationEmittedEvent(init=event_data)
                self._events_stream.on_next(emitted_event)
            except Exception:
                pass

        future_invoke.add_done_callback(publish_invoke_action_event)

        return future_invoke

    def on_event(self, name):
        """Returns an Observable for the Event specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        try:
            self._find_interaction(name, InteractionTypes.EVENT)
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
            self._find_interaction(name, InteractionTypes.PROPERTY)
        except ValueError:
            # noinspection PyUnresolvedReferences
            return Observable.throw(Exception("Unknown property"))

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

        if not self.thing.find_interaction(name=event_name, interaction_type=InteractionTypes.EVENT):
            raise ValueError("Unknown event: {}".format(event_name))

        self._events_stream.on_next(EmittedEvent(name=event_name, init=payload))

    def add_property(self, property_init):
        """Adds a Property defined by the argument and updates the Thing Description.
        Takes an instance of ThingPropertyInit as argument."""

        prop = Property(
            thing=self._thing,
            name=property_init.name,
            output_data=property_init.type,
            writable=property_init.writable,
            observable=property_init.observable)

        property_init.copy_annotations_to_interaction(prop)

        self._thing.add_interaction(prop)
        self._set_property_value(prop, property_init.value)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.PROPERTY,
            method=TDChangeMethod.ADD,
            name=property_init.name,
            data=property_init,
            description=self._thing.to_jsonld_dict())

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def remove_property(self, name):
        """Removes the Property specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name, interaction_type=InteractionTypes.PROPERTY)

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
            name=action_init.name,
            output_data=action_init.output_data_description,
            input_data=action_init.input_data_description)

        action_init.copy_annotations_to_interaction(action)

        self._thing.add_interaction(action)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.ACTION,
            method=TDChangeMethod.ADD,
            name=action_init.name,
            data=action_init,
            description=self._thing.to_jsonld_dict())

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def remove_action(self, name):
        """Removes the Action specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name, interaction_type=InteractionTypes.ACTION)

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
            name=event_init.name,
            output_data=event_init.data_description)

        event_init.copy_annotations_to_interaction(event)

        self._thing.add_interaction(event)

        event_data = ThingDescriptionChangeEventInit(
            td_change_type=TDChangeType.EVENT,
            method=TDChangeMethod.ADD,
            name=event_init.name,
            data=event_init,
            description=self._thing.to_jsonld_dict())

        self._events_stream.on_next(ThingDescriptionChangeEmittedEvent(init=event_data))

    def remove_event(self, name):
        """Removes the event specified by the name argument,
        updates the Thing Description and returns the object."""

        self._thing.remove_interaction(name, interaction_type=InteractionTypes.EVENT)

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
            interaction = self._find_interaction(
                interaction_name=action_name,
                interaction_type=InteractionTypes.ACTION)

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
            interaction = self._find_interaction(
                interaction_name=property_name,
                interaction_type=InteractionTypes.PROPERTY)

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
            interaction = self._find_interaction(
                interaction_name=property_name,
                interaction_type=InteractionTypes.PROPERTY)

        self._set_handler(
            handler_type=self.HandlerKeys.UPDATE_PROPERTY,
            handler=write_handler,
            interaction=interaction)
