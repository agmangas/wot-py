#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent Scripting API dictionaries.
"""

from wotpy.wot.enums import DiscoveryMethod, TDChangeType, TDChangeMethod


class SemanticType(object):
    """Represents a semantic type annotation, containing a
    name, a context and an optional prefix."""

    def __init__(self, name, context, prefix=None):
        self.name = name
        self.context = context
        self.prefix = prefix

    def __eq__(self, other):
        return self.name == other.name and \
               self.context == other.context and \
               self.prefix == other.prefix

    def __hash__(self):
        return hash((self.name, self.context, self.prefix))


class SemanticMetadata(object):
    """Represents a semantic metadata item, containing a
    semantic type (the predicate) and a value (the object)."""

    def __init__(self, semantic_type, value):
        self.semantic_type = semantic_type
        self.value = value

    def __eq__(self, other):
        return self.semantic_type == other.semantic_type and \
               self.value == self.value

    def __hash__(self):
        return hash((self.semantic_type, self.value))


class SemanticAnnotations(object):
    """Represents a tuple of sequences of semantic types and semantic metadata items."""

    def __init__(self, semantic_types=None, metadata=None):
        self.semantic_types = set(semantic_types) if semantic_types else set()
        self.metadata = set(metadata) if metadata else set()

    def __eq__(self, other):
        return self.semantic_types == other.semantic_types and \
               self.metadata == self.metadata

    def __hash__(self):
        return hash((self.semantic_types, self.metadata))

    @property
    def contexts(self):
        """Returns a list of dicts that represent all contexts referenced in these annotations.
        Each dict contains a 'context' key and an optional 'prefix' key."""

        sem_types_metadata = set([item.semantic_type for item in self.metadata])
        sem_types_all = self.semantic_types.union(sem_types_metadata)

        return [{"context": item.context, "prefix": item.prefix} for item in sem_types_all]

    def _copy_contexts(self, thing_sem_context):
        """Copy the local context to the given ThingSemanticContext."""

        for item in self.contexts:
            thing_sem_context.add(context_url=item["context"], prefix=item["prefix"])

    def _copy_types(self, thing_sem_types):
        """Copy the local types to the given ThingSemanticTypes."""

        for sem_type in self.semantic_types:
            thing_sem_types.add(sem_type.name)

    def _copy_metadata(self, thing_sem_metadata):
        """Copy the local metadata to the given ThingSemanticMetadata."""

        for sem_meta in self.metadata:
            sem_type = sem_meta.semantic_type
            key = "{}:{}".format(sem_type.prefix, sem_type.name) if sem_type.prefix else sem_type.name
            thing_sem_metadata.add(key=key, val=sem_meta.value)

    def copy_annotations_to_interaction(self, interaction):
        """Copy these semantic annotations to the given Interaction object."""

        self._copy_contexts(interaction.thing.semantic_context)
        self._copy_types(interaction.semantic_types)
        self._copy_metadata(interaction.semantic_metadata)

    def copy_annotations_to_thing(self, thing):
        """Copy these semantic annotations to the given Thing object."""

        self._copy_contexts(thing.semantic_context)
        self._copy_types(thing.semantic_types)
        self._copy_metadata(thing.semantic_metadata)


class ThingFilter(object):
    """Represents a filter that may be applied
    to a things discovery operation."""

    def __init__(self, method=DiscoveryMethod.ANY, url=None, query=None, contraints=None):
        assert method in DiscoveryMethod.list()
        self.method = method
        self.url = url
        self.query = query
        self.contraints = contraints


class ThingTemplate(SemanticAnnotations):
    """A Thing Template is a dictionary that provides a user
    given name, and the semantic types and semantic metadata
    attached to the ExposedThing Thing Description's root level."""

    def __init__(self, name, semantic_types=None, metadata=None):
        self.name = name

        super(ThingTemplate, self).__init__(semantic_types=semantic_types, metadata=metadata)


class ThingPropertyInit(SemanticAnnotations):
    """Represents the set of properties required to initialize a thing property."""

    def __init__(self, name, data_type,
                 value=None, writable=True, observable=True,
                 semantic_types=None, metadata=None):
        self.name = name
        self.data_type = data_type
        self.value = value
        self.writable = writable
        self.observable = observable

        super(ThingPropertyInit, self).__init__(semantic_types=semantic_types, metadata=metadata)

    @property
    def type(self):
        """Data type property."""

        return self.data_type

    def __eq__(self, other):
        return super(ThingPropertyInit, self).__eq__(other) and \
               self.name == other.name and \
               self.type == other.type and \
               self.value == other.value and \
               self.writable == other.writable and \
               self.observable == other.observable

    def __hash__(self):
        return hash((
            super(ThingPropertyInit, self).__hash__(),
            self.name,
            self.type,
            self.value,
            self.writable,
            self.observable
        ))


class ThingActionInit(SemanticAnnotations):
    """Represents the set of properties required to initialize a thing action."""

    def __init__(self, name,
                 input_data_description=None, output_data_description=None,
                 semantic_types=None, metadata=None):
        self.name = name
        self.input_data_description = input_data_description
        self.output_data_description = output_data_description

        super(ThingActionInit, self).__init__(semantic_types=semantic_types, metadata=metadata)

    def __eq__(self, other):
        return super(ThingActionInit, self).__eq__(other) and \
               self.name == other.name and \
               self.input_data_description == other.input_data_description and \
               self.output_data_description == other.output_data_description

    def __hash__(self):
        return hash((
            super(ThingActionInit, self).__hash__(),
            self.name,
            self.input_data_description,
            self.output_data_description
        ))


class ThingEventInit(SemanticAnnotations):
    """Represents the set of properties required to initialize a thing event."""

    def __init__(self, name,
                 data_description=None,
                 semantic_types=None, metadata=None):
        self.name = name
        self.data_description = data_description

        super(ThingEventInit, self).__init__(semantic_types=semantic_types, metadata=metadata)

    def __eq__(self, other):
        return super(ThingEventInit, self).__eq__(other) and \
               self.name == other.name and \
               self.data_description == other.data_description

    def __hash__(self):
        return hash((
            super(ThingEventInit, self).__hash__(),
            self.name,
            self.data_description
        ))


class PropertyChangeEventInit(object):
    """Represents the data contained in a property update event.

    Args:
        name (str): Name of the property
        value (int): Value of the property
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value


class ActionInvocationEventInit(object):
    """Represents the data contained in an action invocation event.

    Args:
        action_name (str): Name of the property
        return_value: Result returned by the action invocation
    """

    def __init__(self, action_name, return_value):
        self.action_name = action_name
        self.return_value = return_value


class ThingDescriptionChangeEventInit(object):
    """Represents the data contained in a thing description update event.

    Args:
        td_change_type (str): An item of enumeration :py:class:`.TDChangeType`
        method (str): An item of enumeration :py:class:`.TDChangeMethod`
        name (str): Name of the Interaction
        data (int): An instance of :py:class:`.ThingPropertyInit`, :py:class:`.ThingActionInit`
            or :py:class:`.ThingEventInit` (or ``None`` if no interaction was added to the TD)
        description (object): A dict that represents a TD serialized to JSON-LD
    """

    def __init__(self, td_change_type, method, name, data=None, description=None):
        assert td_change_type in TDChangeType.list()
        assert method in TDChangeMethod.list()
        assert data is None or isinstance(data, (ThingPropertyInit, ThingActionInit, ThingEventInit))

        self.td_change_type = td_change_type
        self.method = method
        self.name = name
        self.data = data
        self.description = description
