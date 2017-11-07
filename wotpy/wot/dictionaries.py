#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.wot.enums import DiscoveryMethod, TDChangeType, TDChangeMethod


class ThingFilter(object):
    """Represents a filter that may be applied
    to a things discovery operation."""

    def __init__(self, url, description, method=DiscoveryMethod.ANY):
        assert method in DiscoveryMethod.list()
        self.discovery_type = method
        self.url = url
        self.description = description


class ThingInit(object):
    """Represents the set of properties required
    to create a locally hosted thing."""

    def __init__(self, name=None, url=None, description=None):
        """Constructor. If description is None a basic empty
        thing description document will be used instead."""

        assert name or url or description, "Please define at least one argument"

        self.name = name
        self.url = url
        self.description = description


class SemanticType(object):
    """Represents a semantic type annotation, containing a name and a context."""

    def __init__(self, name, context):
        self.name = name
        self.context = context


class ThingPropertyInit(object):
    """Represents the set of properties required to initialize a thing property."""

    def __init__(self, name, value, description, configurable=False,
                 enumerable=True, writable=True, semantic_types=None):
        self.name = name
        self.value = value
        self.description = description
        self.configurable = configurable
        self.enumerable = enumerable
        self.writable = writable
        self.semantic_types = semantic_types if semantic_types else []


class ThingEventInit(object):
    """Represents the set of properties required to initialize a thing event."""

    def __init__(self, name, data_description, semantic_types=None):
        self.name = name
        self.data_description = data_description
        self.semantic_types = semantic_types if semantic_types else []


class ThingActionInit(object):
    """Represents the set of properties required to initialize a thing action."""

    def __init__(self, name, action, input_data_description,
                 output_data_description, semantic_types=None):
        self.name = name
        self.action = action
        self.input_data_description = input_data_description
        self.output_data_description = output_data_description
        self.semantic_types = semantic_types if semantic_types else []


class PropertyChangeEventInit(object):
    """Represents a change Property."""

    def __init__(self, name, value):
        self.name = name
        self.value = value


class ActionInvocationEventInit(object):
    """Represents the notification data from the Action invocation."""

    def __init__(self, action_name, return_value):
        self.action_name = action_name
        self.return_value = return_value


class ThingDescriptionChangeEventInit(object):
    """The data attribute represents the changes that occurred to the Thing Description."""

    def __init__(self, td_change_type, method, name, data=None, description=None):
        assert td_change_type in TDChangeType.list()
        assert method in TDChangeMethod.list()
        assert data is None or isinstance(data, (ThingPropertyInit, ThingActionInit, ThingEventInit))

        self.td_change_type = td_change_type
        self.method = method
        self.name = name
        self.data = data
        self.description = description


class Request(object):
    """Represents an incoming request the ExposedThing is supposed to handle, for instance
    retrieving and updating properties, invoking Actions and observing Events (WoT interactions)."""

    def __init__(self, request_type, name, respond=None, respond_with_error=None,
                 request_from=None, options=None, data=None):
        assert respond is None or callable(respond)
        assert respond_with_error is None or callable(respond_with_error)

        self.request_type = request_type
        self.name = name
        self.respond = respond
        self.respond_with_error = respond_with_error
        self.request_from = request_from
        self.options = options
        self.data = data
