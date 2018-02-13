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

    @classmethod
    def sequence_to_jsonld_context(cls, semantic_types):
        """Returns an array of semantic contexts that represents the context field of a
        serialized JSON-LD document. This context is built from a sequence of SemanticTypes."""

        types_unique_ctx = []

        for sem_type in semantic_types:
            try:
                next(item for item in types_unique_ctx if item.is_equal_context(sem_type))
            except StopIteration:
                types_unique_ctx.append(sem_type)

        ret = []

        for sem_type in types_unique_ctx:
            if sem_type.prefix:
                ret.append({sem_type.prefix: sem_type.context})
            else:
                ret.append(sem_type.context)

        return ret

    @classmethod
    def sequence_to_jsonld_types(cls, semantic_types):
        """Returns an array of semantic types that represents the types field of a
        serialized JSON-LD document. This context is built from a sequence of SemanticTypes."""

        ret = []

        for sem_type in semantic_types:
            if sem_type.prefix:
                ret.append("{}:{}".format(sem_type.prefix, sem_type.name))
            else:
                ret.append(sem_type.name)

        return ret

    def is_equal_context(self, other):
        """Returns True if the context of the given SemanticType is equal to this one."""

        return self.context == other.context and self.prefix == other.prefix


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

    @property
    def merged_semantic_types(self):
        """Returns a list containing all SemanticTypes
        from the internal metadata and types sequences."""

        return list(set([item.semantic_type for item in self.metadata]).union(self.semantic_types))

    def add_semantic_type(self, semantic_type):
        """Add a new SemanticType item."""

        self.semantic_types.add(semantic_type)

    def remove_semantic_type(self, semantic_type):
        """Remove an existing SemanticType item."""

        self.semantic_types.discard(semantic_type)

    def add_semantic_metadata(self, semantic_metadata):
        """Add a new SemanticMetadata item."""

        self.metadata.add(semantic_metadata)

    def remove_semantic_metadata(self, semantic_metadata):
        """Remove an existing SemanticMetadata item."""

        self.metadata.discard(semantic_metadata)

    def to_jsonld_types(self):
        """Returns an array of semantic types that represents
        the types field of a JSON-LD serialized document."""

        return SemanticType.sequence_to_jsonld_types(self.semantic_types)
