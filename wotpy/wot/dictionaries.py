#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Classes that represent wrappers for dictionaries described in the Scripting API document.
"""

import six

from wotpy.wot.enums import TDChangeType, TDChangeMethod, JSONType


def _build_init_dict(args, kwargs):
    """Takes a tuple of args and dict of kwargs and updates the kwargs dict
    with the first argument of args (if that item is a dict)."""

    init_dict = {}

    if len(args) > 0 and isinstance(args[0], dict):
        init_dict = args[0]

    init_dict.update(kwargs)

    return init_dict


class ThingTemplateDictionary(object):
    """ThingTemplate is a wrapper around a dictionary that contains properties
    representing semantic metadata and interactions (Properties, Actions and Events).
    It is used for initializing an internal representation of a Thing Description,
    and it is also used in ThingFilter."""

    def __init__(self, *args, **kwargs):
        self._init = _build_init_dict(args, kwargs)

        if self.id is None:
            raise ValueError("Thing ID is required")

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return self._init

    @property
    def name(self):
        """The name attribute represents the name of the Thing."""

        return self._init.get("name", self.id)

    @property
    def id(self):
        """The id optional attribute represents an application provided hint
        for the unique identifier of the Thing, typically a URI, IRI, or URN.
        Note that the WoT Runtime may override this with a different value when exposing the Thing."""

        return self._init.get("id")

    @property
    def description(self):
        """The description optional attribute represents
        a human readable description of the Thing."""

        return self._init.get("description")

    @property
    def support(self):
        """The support optional attribute represents human
        readable information about the TD maintainer."""

        return self._init.get("support")

    @property
    def security(self):
        """The security optional attribute represents security metadata."""

        return self._init.get("security")

    @property
    def properties(self):
        """The properties optional attribute represents a dict with keys
        that correspond to Property names and values of type PropertyInit."""

        return self._init.get("properties", {})

    @property
    def actions(self):
        """The actions optional attribute represents a dict with keys
        that correspond to Action names and values of type ActionInit."""

        return self._init.get("actions", {})

    @property
    def events(self):
        """The events optional attribute represents a dictionary with keys
        that correspond to Event names and values of type EventInit."""

        return self._init.get("events", {})

    @property
    def links(self):
        """The links optional attribute represents an array of WebLink objects."""

        return [WebLinkDictionary(item) for item in self._init.get("links", [])]

    @property
    def context(self):
        """The @context optional attribute represents a semantic context."""

        return self._init.get("@context")

    @property
    def type(self):
        """The @type optional attribute represents a semantic type."""

        return self._init.get("@type")


class SecurityDictionary(object):
    """Contains security related configuration."""

    def __init__(self, *args, **kwargs):
        self._init = _build_init_dict(args, kwargs)

        if self.scheme is None:
            raise ValueError("Property 'scheme' is required")

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return self._init

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return self._init.get("scheme")

    @property
    def in_data(self):
        """The in property represents security initialization data
        as described in the Security metadata description document."""

        return self._init.get("in")


class ThingFilterDictionary(object):
    """The ThingFilter dictionary that represents the
    constraints for discovering Things as key-value pairs."""

    def __init__(self, *args, **kwargs):
        self._init = _build_init_dict(args, kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return self._init

    @property
    def method(self):
        """The method property represents the discovery type
        that should be used in the discovery process."""

        return self._init.get("method")

    @property
    def url(self):
        """The url property represents additional information for the discovery method,
        such as the URL of the target entity serving the discovery request,
        for instance a Thing Directory (if method is "directory") or a Thing (otherwise)."""

        return self._init.get("url")

    @property
    def query(self):
        """The query property represents a query string accepted by the implementation,
        for instance a SPARQL or JSON query. Support may be implemented locally in the
        WoT Runtime or remotely as a service in a Thing Directory."""

        return self._init.get("query")

    @property
    def template(self):
        """The template property represents a ThingTemplate dictionary
        wrapper class used for matching against discovered Things."""

        template = self._init.get("template")

        return None if template is None else ThingTemplateDictionary(template)


class LinkDictionary(object):
    """A link to an external resource that may be related to the Thing in any way."""

    def __init__(self, *args, **kwargs):
        self._init = _build_init_dict(args, kwargs)

        if self.href is None:
            raise ValueError("Property 'href' is required")

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return self._init

    @property
    def href(self):
        """The href property is a hypertext reference that defines the Link."""

        return self._init.get("href")

    @property
    def media_type(self):
        """The mediaType property represents the IANA media type associated with the Link."""

        return self._init.get("mediaType", self._init.get("media_type"))

    @property
    def rel(self):
        """The rel property represents a semantic label that
        specifies how to interact with the linked resource."""

        return self._init.get("rel")


class WebLinkDictionary(LinkDictionary):
    """A Link from a Thing to a resource that exists on the Web."""

    def __init__(self, *args, **kwargs):
        super(WebLinkDictionary, self).__init__(*args, **kwargs)

    @property
    def anchor(self):
        """The anchor property represents a URI that
        overrides the default context of a Link."""

        return self._init.get("anchor")


class FormDictionary(LinkDictionary):
    """A dictionary that describes a connection endpoint for an interaction."""

    def __init__(self, *args, **kwargs):
        super(FormDictionary, self).__init__(*args, **kwargs)

    @property
    def security(self):
        """The security property represents the security
        requirements for the linked resource."""

        return self._init.get("security")


class DataSchemaDictionary(object):
    """Represents the common properties of a value type definition."""

    def __init__(self, *args, **kwargs):
        self._init = _build_init_dict(args, kwargs)

        if self.type is None:
            raise ValueError("Property 'type' is required")

    @classmethod
    def build(cls, *args, **kwargs):
        """Builds an instance of the appropriate subclass for the given ValueType."""

        init_dict = _build_init_dict(args, kwargs)

        klass_map = {
            JSONType.NUMBER: NumberSchemaDictionary,
            JSONType.BOOLEAN: BooleanSchemaDictionary,
            JSONType.STRING: StringSchemaDictionary,
            JSONType.OBJECT: ObjectSchemaDictionary,
            JSONType.ARRAY: ArraySchemaDictionary
        }

        klass_type = init_dict.get("type")
        klass = klass_map.get(klass_type)

        if not klass:
            raise ValueError("Unknown type: {}".format(klass_type))

        return klass(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return {
            "type": self.type,
            "required": self.required,
            "description": self.description,
            "const": self.const
        }

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return self._init.get("type")

    @property
    def required(self):
        """The required property tells whether this value is required to be specified."""

        return self._init.get("required", False)

    @property
    def description(self):
        """The description property represents a textual description of the value."""

        return self._init.get("description")

    @property
    def const(self):
        """The const property tells whether this value is constant."""

        return self._init.get("const")


class NumberSchemaDictionary(DataSchemaDictionary):
    """Properties to describe a numeric type."""

    def __init__(self, *args, **kwargs):
        super(NumberSchemaDictionary, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(NumberSchemaDictionary, self).to_dict()

        ret.update({
            "minimum": self.minimum,
            "maximum": self.maximum
        })

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.NUMBER

    @property
    def minimum(self):
        """The minimum property may be present when the value is of type
        number and if present, it defines the minimum value that can be used."""

        return self._init.get("minimum")

    @property
    def maximum(self):
        """The maximum property may be present when the value is of type
        number and if present, it defines the maximum value that can be used."""

        return self._init.get("maximum")


class BooleanSchemaDictionary(DataSchemaDictionary):
    """Properties to describe a boolean type."""

    def __init__(self, *args, **kwargs):
        super(BooleanSchemaDictionary, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(BooleanSchemaDictionary, self).to_dict()

        ret.update({})

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.BOOLEAN


class StringSchemaDictionary(DataSchemaDictionary):
    """Properties to describe a string type."""

    def __init__(self, *args, **kwargs):
        super(StringSchemaDictionary, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(StringSchemaDictionary, self).to_dict()

        ret.update({
            "enum": self.enum
        })

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.STRING

    @property
    def enum(self):
        """The enum property represents the list of allowed string values as a string array."""

        return self._init.get("enum", [])


class ObjectSchemaDictionary(DataSchemaDictionary):
    """Properties to describe an object type."""

    def __init__(self, *args, **kwargs):
        super(ObjectSchemaDictionary, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(ObjectSchemaDictionary, self).to_dict()

        ret.update({
            "properties": {
                key: val_type.to_dict()
                for key, val_type in six.iteritems(self.properties)
            },
            "required": self.required
        })

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.OBJECT

    @property
    def properties(self):
        """The properties property is a dictionary that contains the object properties."""

        return {
            key: DataSchemaDictionary.build(val)
            for key, val in six.iteritems(self._init.get("properties", {}))
        }

    @property
    def required(self):
        """The required property is a string array that containes the names
        that are mandatory to be present from the object properties."""

        return self._init.get("required", [])


class ArraySchemaDictionary(DataSchemaDictionary):
    """Properties to describe an array type."""

    def __init__(self, *args, **kwargs):
        super(ArraySchemaDictionary, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(ArraySchemaDictionary, self).to_dict()

        ret.update({
            "items": [val_type.to_dict() for val_type in self.items],
            "minItems": self.min_items,
            "maxItems": self.max_items
        })

        return ret

    @property
    def type(self):
        """The type property represents the value type enumerated in JSONType."""

        return JSONType.ARRAY

    @property
    def items(self):
        """The items property is an array of ValueType elements."""

        return [DataSchemaDictionary.build(item) for item in self._init.get("items", [])]

    @property
    def min_items(self):
        """The minItems property represents the minimum
        number of elements required to be in the array."""

        return self._init.get("minItems", self._init.get("min_items"))

    @property
    def max_items(self):
        """The maxItems property represents the maximum
        number of elements that can be specified in the array."""

        return self._init.get("maxItems", self._init.get("max_items"))


class InteractionInitDictionary(object):
    """A dictionary wrapper class that contains data to initialize an Interaction."""

    def __init__(self, *args, **kwargs):
        self._init = _build_init_dict(args, kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties"""

        return {
            "label": self.label,
            "forms": [item.to_dict() for item in self.forms],
            "links": [item.to_dict() for item in self.links],
        }

    @property
    def label(self):
        """The label property initializes the text label for the interaction."""

        return self._init.get("label")

    @property
    def forms(self):
        """The forms read-only property initializes the
        protocol bindings initialization data."""

        return [FormDictionary(item) for item in self._init.get("forms", [])]

    @property
    def links(self):
        """The links read-only property initializes the
        array of Links attached to the interaction."""

        return [LinkDictionary(item) for item in self._init.get("links", [])]


class PropertyInitDictionary(InteractionInitDictionary):
    """A dictionary wrapper class that contains data to initialize a Property."""

    def __init__(self, *args, **kwargs):
        super(PropertyInitDictionary, self).__init__(*args, **kwargs)
        self._data_schema = DataSchemaDictionary.build(self._init)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal ValueType before propagating the exception."""

        return self.data_schema.__getattribute__(name)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties"""

        base_dict = super(PropertyInitDictionary, self).to_dict()

        base_dict.update({
            "writable": self.writable,
            "observable": self.observable,
            "value": self.value
        })

        base_dict.update(self.data_schema.to_dict())

        return base_dict

    @property
    def data_schema(self):
        """The DataSchemaDictionary wrapper that represents the schema of this interaction."""

        return self._data_schema

    @property
    def writable(self):
        """The writable property initializes access to the Property value.
        The default value is false."""

        return self._init.get("writable", False)

    @property
    def observable(self):
        """The observable property initializes observability access to the Property.
        The default value is false."""

        return self._init.get("observable", False)

    @property
    def value(self):
        """The value property represents the initialization value of the property.
        Its type should match the one defined in the type property."""

        return self._init.get("value")


class ActionInitDictionary(InteractionInitDictionary):
    """A dictionary wrapper class that contains data to initialize an Action."""

    def __init__(self, *args, **kwargs):
        super(ActionInitDictionary, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties"""

        base_dict = super(ActionInitDictionary, self).to_dict()

        base_dict.update({
            "description": self.description
        })

        if self.input:
            base_dict.update({"input": self.input.to_dict()})

        if self.output:
            base_dict.update({"output": self.output.to_dict()})

        return base_dict

    @property
    def input(self):
        """The input property initializes the input of type ValueType to the ThingAction.
        Multiple arguments can be provided by applications as an array or as an object."""

        init = self._init.get("input")

        return DataSchemaDictionary.build(init) if init else None

    @property
    def output(self):
        """The output property initializes the output of type ValueType of the ThingAction.
        The value is overridden when the action is executed."""

        init = self._init.get("output")

        return DataSchemaDictionary.build(init) if init else None

    @property
    def description(self):
        """The description read-only property initializes a
        human-readable textual description of the Action interaction."""

        return self._init.get("description")


class EventInitDictionary(PropertyInitDictionary):
    """A dictionary wrapper class that contains data to initialize an Event."""

    pass


class PropertyChangeEventInit(object):
    """Represents the data contained in a property update event.

    Args:
        name (str): Name of the property.
        value: Value of the property.
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value


class ActionInvocationEventInit(object):
    """Represents the data contained in an action invocation event.

    Args:
        action_name (str): Name of the property.
        return_value: Result returned by the action invocation.
    """

    def __init__(self, action_name, return_value):
        self.action_name = action_name
        self.return_value = return_value


class ThingDescriptionChangeEventInit(object):
    """Represents the data contained in a thing description update event.

    Args:
        td_change_type (str): An item of enumeration :py:class:`.TDChangeType`.
        method (str): An item of enumeration :py:class:`.TDChangeMethod`.
        name (str): Name of the Interaction.
        data: An instance of :py:class:`.ThingPropertyInit`, :py:class:`.ThingActionInit`
            or :py:class:`.ThingEventInit` (or ``None`` if the change did not add a new interaction).
        description (dict): A dict that represents a TD serialized to JSON-LD.
    """

    def __init__(self, td_change_type, method, name, data=None, description=None):
        assert td_change_type in TDChangeType.list()
        assert method in TDChangeMethod.list()

        self.td_change_type = td_change_type
        self.method = method
        self.name = name
        self.data = data
        self.description = description
