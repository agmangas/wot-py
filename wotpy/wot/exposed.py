#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.td.description import ThingDescription


class ThingPropertyInit(object):
    """Represents the set of properties required to initialize a thing property."""

    def __init__(self, name, value, configurable=True, enumerable=True,
                 writable=True, semantic_types=None, data_description=None):
        self.name = name
        self.value = value
        self.configurable = configurable
        self.enumerable = enumerable
        self.writable = writable
        self.semantic_types = semantic_types
        self.data_description = data_description


class ThingEventInit(object):
    """Represents the set of properties required to initialize a thing event."""

    def __init__(self, name, semantic_types=None, output_data_description=None):
        self.name = name
        self.semantic_types = semantic_types
        self.output_data_description = output_data_description


class ThingActionInit(object):
    """Represents the set of properties required to initialize a thing action."""

    def __init__(self, name, action, input_data_description=None,
                 output_data_description=None, semantic_types=None):
        self.name = name
        self.action = action
        self.input_data_description = input_data_description
        self.output_data_description = output_data_description
        self.semantic_types = semantic_types


class PropertyRequest(object):
    """Represents the information that is passed to the callback
    that gets called when a property is updated or retrieved."""

    def __init__(self, request_from, thing_property_init, options):
        self.request_from = request_from
        self.thing_property_init = thing_property_init
        self.options = options


class ActionRequest(object):
    """Represents the information that is passed to the
    callback that gets called when an action is invoked."""

    def __init__(self, request_from, thing_action_init, input_data):
        self.request_from = request_from
        self.thing_action_init = thing_action_init
        self.input_data = input_data


class ObserveRequest(object):
    """Represents the information that is passed to the callback
    that gets called when the thing receives an observe request."""

    def __init__(self, request_from, observe_type, subscribe, name):
        assert observe_type in ObserveType.list()
        self.request_from = request_from
        self.observe_type = observe_type
        self.subscribe = subscribe
        self.name = name


class ObserveType(object):
    """Enumeration of observable types."""

    PROPERTY = 'property',
    ACTION = 'action',
    EVENT = 'event',
    TD = 'td'

    @classmethod
    def list(cls):
        """Returns a list with all observable types."""

        return [cls.PROPERTY, cls.ACTION, cls.EVENT, cls.TD]


class ExposedThing(object):
    """An entity that serves to define the behavior of a Thing.
    An application uses this class when it acts as the Thing 'server'."""

    def __init__(self, servient, name, url, description):
        self._servient = servient
        self._name = name
        self._url = url
        self._thing_description = ThingDescription(description)

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

        return self._thing_description.doc

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

    def add_property(self, thing_property_init):
        """Takes a ThingPropertyInit instance and
        creates a new property in this thing."""

        pass

    def remove_property(self, name):
        """Removes an existing property by name."""

        pass

    def add_action(self, thing_action_init):
        """Takes a ThingActionInit instance and
        creates a new action in this thing."""

        pass

    def remove_action(self, name):
        """Removes an existing action by name."""

        pass

    def add_event(self, thing_event_init):
        """Takes a ThingEventInit instance and
        creates a new event in this thing."""

        pass

    def remove_event(self, name):
        """Removes an existing event by name."""

        pass

    def register(self, directory=None):
        """Register this thing in a directory.
        Returns a Future that resolves when the operation has completed."""

        pass

    def unregister(self):
        """Unregister this thing from a directory.
        Returns a Future that resolves when the operation has completed."""

        pass

    def start(self):
        """"""

        pass

    def stop(self):
        """"""

        pass

    def emit_event(self, event_name, payload):
        """Emits an event."""

        pass

    def on_retrieve_property(self, handler):
        """Callback called when a property is retrieved.
        The handler is a function that takes an argument of type PropertyRequest."""

        pass

    def on_update_property(self, handler):
        """Callback called when a property is updated.
        The handler is a function that takes an argument of type PropertyRequest."""

        pass

    def on_invoke_action(self, handler):
        """Callback called when an action is invoked.
        The handler is a function that takes an argument of type ActionRequest."""

        pass

    def on_observe(self, handler):
        """Callback called when an observe request is received.
        The handler is a function that takes an argument of type ObserveRequest."""

        pass
