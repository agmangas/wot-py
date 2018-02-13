#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

# noinspection PyCompatibility
from concurrent.futures import Future, ThreadPoolExecutor
from rx import Observable
from rx.subjects import Subject
from six import string_types
from tornado.httpclient import HTTPClient, HTTPRequest

from wotpy.td.enums import InteractionTypes
from wotpy.td.interaction import Property, Action, Event
from wotpy.td.thing import Thing
from wotpy.td.jsonld.thing import JsonLDThingDescription
from wotpy.utils.enums import EnumListMixin
from wotpy.utils.futures import is_future
from wotpy.wot.dictionaries import \
    Request, \
    PropertyChangeEventInit, \
    ThingDescriptionChangeEventInit, \
    ActionInvocationEventInit
from wotpy.wot.enums import \
    RequestType, \
    DefaultThingEvent, \
    TDChangeMethod, \
    TDChangeType
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
        ACTION_FUNCTIONS = "action_functions"

    def __init__(self, servient, thing):
        self._servient = servient
        self._thing = thing

        self._interaction_states = {
            self.InteractionStateKeys.PROPERTY_VALUES: {},
            self.InteractionStateKeys.ACTION_FUNCTIONS: {}
        }

        self._handlers_global = {
            self.HandlerKeys.RETRIEVE_PROPERTY: self._default_retrieve_property_handler,
            self.HandlerKeys.UPDATE_PROPERTY: self._default_update_property_handler,
            self.HandlerKeys.INVOKE_ACTION: self._default_invoke_action_handler,
            self.HandlerKeys.OBSERVE: self._default_observe_handler
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

        # ToDo: Keep semantic annotations

        jsonld_td = JsonLDThingDescription(doc=doc)

        name = name or jsonld_td.name
        thing = Thing(name=name)

        def _build_property(jsonld_inter):
            return Property(
                thing=thing,
                name=jsonld_inter.name,
                output_data=jsonld_inter.output_data,
                writable=jsonld_inter.writable)

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

            for item in (jsonld_interaction.type or []):
                interaction.add_type(item)

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

    def _set_action_func(self, action, func):
        """Sets the action function of an Action."""

        action_funcs = self.InteractionStateKeys.ACTION_FUNCTIONS
        self._interaction_states[action_funcs][action] = func

    def _get_action_func(self, action):
        """Returns the action function of an Action."""

        action_funcs = self.InteractionStateKeys.ACTION_FUNCTIONS
        return self._interaction_states[action_funcs].get(action, None)

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

    def _default_retrieve_property_handler(self, request):
        """Default handler for onRetrieveProperty."""

        future_ret = Future()

        try:
            assert request.request_type == RequestType.PROPERTY and \
                   request.name

            prop = self._find_interaction(
                interaction_name=request.name,
                interaction_type=InteractionTypes.PROPERTY)

            prop_value = self._get_property_value(prop)

            request.respond and request.respond(prop_value)
            future_ret.set_result(prop_value)
        except Exception as ex:
            request.respond_with_error and request.respond_with_error(ex)
            future_ret.set_exception(ex)

        return future_ret

    def _default_update_property_handler(self, request):
        """Default handler for onUpdateProperty."""

        future_ret = Future()

        try:
            assert request.request_type == RequestType.PROPERTY and \
                   request.name and \
                   hasattr(request, "data")

            prop = self._find_interaction(
                interaction_name=request.name,
                interaction_type=InteractionTypes.PROPERTY)

            self._set_property_value(prop, request.data)

            request.respond and request.respond()
            future_ret.set_result(None)
        except Exception as ex:
            request.respond_with_error and request.respond_with_error(ex)
            future_ret.set_exception(ex)

        return future_ret

    def _default_invoke_action_handler(self, request):
        """Default handler for onInvokeAction."""

        future_ret = Future()

        try:
            assert request.request_type == RequestType.ACTION and \
                   request.name

            input_kwargs = request.data if hasattr(request, "data") else {}

            assert isinstance(input_kwargs, dict)

            action = self._find_interaction(
                interaction_name=request.name,
                interaction_type=InteractionTypes.ACTION)

            action_func = self._get_action_func(action)

            assert callable(action_func), "No action defined for: {}".format(request.name)

            action_result = action_func(**input_kwargs)

            def _respond_callback(ft):
                completed_result = ft.result()
                request.respond(completed_result)
                future_ret.set_result(completed_result)

            if is_future(action_result):
                action_result.add_done_callback(_respond_callback)
            else:
                request.respond and request.respond(action_result)
                future_ret.set_result(action_result)
        except Exception as ex:
            request.respond_with_error and request.respond_with_error(ex)
            future_ret.set_exception(ex)

        return future_ret

    def _default_observe_handler(self, request):
        """Default handler for onObserve."""

        def _build_property_filter():
            """Returns a filter that can be appended to the global events
            stream to generate an Observable for property update events."""

            prop_name = request.name

            self._find_interaction(
                interaction_name=prop_name,
                interaction_type=InteractionTypes.PROPERTY)

            def _filter_func(item):
                return item.name == DefaultThingEvent.PROPERTY_CHANGE and \
                       item.data.name == prop_name

            return _filter_func

        def _build_event_filter():
            """Returns a filter that can be appended to the global events
            stream to generate an Observable for custom events defined in the TD."""

            event_name = request.name

            self._find_interaction(
                interaction_name=event_name,
                interaction_type=InteractionTypes.EVENT)

            def _filter_func(item):
                return item.name == event_name

            return _filter_func

        def _build_action_filter():
            """Returns a filter that can be appended to the global events
            stream to generate an Observable for custom events defined in the TD."""

            action_name = request.name

            self._find_interaction(
                interaction_name=action_name,
                interaction_type=InteractionTypes.ACTION)

            def _filter_func(item):
                return item.name == DefaultThingEvent.ACTION_INVOCATION and \
                       item.data.action_name == action_name

            return _filter_func

        def _build_td_filter():
            """Returns a filter that can be appended to the global events
            stream to generate an Observable for TD change events."""

            def _filter_func(item):
                return item.name == DefaultThingEvent.DESCRIPTION_CHANGE

            return _filter_func

        try:
            assert request.request_type == RequestType.EVENT and \
                   request.options

            observe_type = request.options.get("observeType")
            subscribe = request.options.get("subscribe", False)

            assert observe_type in RequestType.list()

            filter_builder_map = {
                RequestType.PROPERTY: _build_property_filter,
                RequestType.EVENT: _build_event_filter,
                RequestType.TD: _build_td_filter,
                RequestType.ACTION: _build_action_filter
            }

            if observe_type not in filter_builder_map:
                raise NotImplementedError()

            stream_filter = filter_builder_map[observe_type]()

            # noinspection PyUnresolvedReferences
            observable = self._events_stream.filter(stream_filter)

            if not subscribe:
                observable = observable.first()

            return observable
        except Exception as ex:
            # noinspection PyUnresolvedReferences
            return Observable.throw(ex)

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

    @property
    def thing(self):
        """Internal Thing property."""

        return self._thing

    def get_property(self, name):
        """Takes the Property name as the name argument, then requests from
        the underlying platform and the Protocol Bindings to retrieve the
        Property on the remote Thing and return the result. Returns a Promise
        that resolves with the Property value or rejects with an Error."""

        future_get = Future()

        # noinspection PyUnusedLocal
        def _respond(*resp_args, **resp_kwargs):
            assert len(resp_args), "Must respond with property value"
            future_get.set_result(resp_args[0])

        def _respond_with_error(err):
            future_get.set_exception(err)

        interaction = self._find_interaction(
            interaction_name=name,
            interaction_type=InteractionTypes.PROPERTY)

        handler = self._get_handler(
            handler_type=self.HandlerKeys.RETRIEVE_PROPERTY,
            interaction=interaction)

        request = Request(
            name=name,
            request_type=RequestType.PROPERTY,
            respond=_respond,
            respond_with_error=_respond_with_error)

        handler(request)

        return future_get

    def set_property(self, name, value):
        """Takes the Property name as the name argument and the new value as the
        value argument, then requests from the underlying platform and the Protocol
        Bindings to update the Property on the remote Thing and return the result.
        Returns a Promise that resolves on success or rejects with an Error."""

        future_set = Future()

        # noinspection PyUnusedLocal
        def _respond(*resp_args, **resp_kwargs):
            future_set.set_result(None)

        def _respond_with_error(err):
            future_set.set_exception(err)

        interaction = self._find_interaction(
            interaction_name=name,
            interaction_type=InteractionTypes.PROPERTY)

        handler = self._get_handler(
            handler_type=self.HandlerKeys.UPDATE_PROPERTY,
            interaction=interaction)

        request = Request(
            name=name,
            request_type=RequestType.PROPERTY,
            respond=_respond,
            respond_with_error=_respond_with_error,
            data=value)

        handler(request)

        # noinspection PyUnusedLocal
        def _publish_event(ft):
            event_data = PropertyChangeEventInit(name=name, value=value)
            self._events_stream.on_next(PropertyChangeEmittedEvent(init=event_data))

        future_set.add_done_callback(_publish_event)

        return future_set

    def invoke_action(self, name, **kwargs):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to
        invoke the Action on the remote Thing and return the result. Returns a
        Promise that resolves with the return value or rejects with an Error."""

        future_invoke = Future()

        # noinspection PyUnusedLocal
        def _respond(*resp_args, **resp_kwargs):
            assert len(resp_args), "Must respond with action invocation result"
            future_invoke.set_result(resp_args[0])

        def _respond_with_error(err):
            future_invoke.set_exception(err)

        interaction = self._find_interaction(
            interaction_name=name,
            interaction_type=InteractionTypes.ACTION)

        handler = self._get_handler(
            handler_type=self.HandlerKeys.INVOKE_ACTION,
            interaction=interaction)

        request = Request(
            name=name,
            request_type=RequestType.ACTION,
            respond=_respond,
            respond_with_error=_respond_with_error,
            data=kwargs)

        handler(request)

        # noinspection PyBroadException
        def _publish_event(ft):
            try:
                return_value = ft.result()
                event_data = ActionInvocationEventInit(action_name=name, return_value=return_value)
                emitted_event = ActionInvocationEmittedEvent(init=event_data)
                self._events_stream.on_next(emitted_event)
            except:
                pass

        future_invoke.add_done_callback(_publish_event)

        return future_invoke

    def add_listener(self, event_name, listener):
        """Adds the listener provided in the argument listener to
        the Event name provided in the argument event_name."""

        raise NotImplementedError("Please use observe() instead")

    def remove_listener(self, event_name, listener):
        """Removes a listener from the Event identified by
        the provided event_name and listener argument."""

        raise NotImplementedError("Please use observe() instead")

    def remove_all_listeners(self, event_name=None):
        """Removes all listeners for the Event provided by
        the event_name optional argument, or if that was not
        provided, then removes all listeners from all Events."""

        raise NotImplementedError("Please use observe() instead")

    def observe(self, name=None, request_type=None):
        """Returns an Observable for the Property, Event or Action
        specified in the name argument, allowing subscribing and
        unsubscribing to notifications. The request_type specifies
        whether a Property, an Event or an Action is observed."""

        if request_type is not RequestType.TD and name is None:
            raise ValueError("Name required for requests of type: {}".format(request_type))

        request = Request(
            name=name,
            request_type=RequestType.EVENT,
            options={"observeType": request_type, "subscribe": True})

        handler = self._get_handler(self.HandlerKeys.OBSERVE)
        observable = handler(request)

        return observable

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

        for item in action_init.semantic_types:
            self._thing.add_context(context_url=item.context)
            action.add_type(item.name)

        self._thing.add_interaction(action)
        self._set_action_func(action, action_init.action)

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

        for item in event_init.semantic_types:
            self._thing.add_context(context_url=item.context)
            event.add_type(item.name)

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

    def on_retrieve_property(self, handler, name=None):
        """Registers the handler function for Property retrieve requests received
        for the Thing, as defined by the handler property of type RequestHandler.
        The handler will receive an argument request of type Request where at least
        request.name is defined and represents the name of the Property to be retrieved."""

        interaction = None

        if name is not None:
            interaction = self._find_interaction(
                interaction_name=name,
                interaction_type=InteractionTypes.PROPERTY)

        self._set_handler(
            handler_type=self.HandlerKeys.RETRIEVE_PROPERTY,
            handler=handler,
            interaction=interaction)

    def on_update_property(self, handler, name=None):
        """Defines the handler function for Property update requests received for the Thing,
        as defined by the handler property of type RequestHandler. The handler will receive
        an argument request of type Request where request.name defines the name of the
        Property to be retrieved and request.data defines the new value of the Property."""

        interaction = None

        if name is not None:
            interaction = self._find_interaction(
                interaction_name=name,
                interaction_type=InteractionTypes.PROPERTY)

        self._set_handler(
            handler_type=self.HandlerKeys.UPDATE_PROPERTY,
            handler=handler,
            interaction=interaction)

    def on_invoke_action(self, handler, name=None):
        """Defines the handler function for Action invocation requests received
        for the Thing, as defined by the handler property of type RequestHandler.
        The handler will receive an argument request of type Request where request.name
        defines the name of the Action to be invoked and request.data defines the input
        arguments for the Action as defined by the Thing Description."""

        interaction = None

        if name is not None:
            interaction = self._find_interaction(
                interaction_name=name,
                interaction_type=InteractionTypes.ACTION)

        self._set_handler(
            handler_type=self.HandlerKeys.INVOKE_ACTION,
            handler=handler,
            interaction=interaction)

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

        self._set_handler(handler_type=self.HandlerKeys.OBSERVE, handler=handler)

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

        self._servient.enable_exposed_thing(self.name)

    def stop(self):
        """Stop serving external requests for the Thing."""

        self._servient.disable_exposed_thing(self.name)

    def emit_event(self, event_name, payload):
        """Emits an the event initialized with the event name specified by
        the event_name argument and data specified by the payload argument."""

        if not self.thing.find_interaction(name=event_name, interaction_type=InteractionTypes.EVENT):
            raise ValueError("Unknown event: {}".format(event_name))

        self._events_stream.on_next(EmittedEvent(name=event_name, init=payload))
