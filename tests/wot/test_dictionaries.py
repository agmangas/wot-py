#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import pytest
import six
from faker import Faker

from wotpy.wot.dictionaries.interaction import PropertyFragmentDict, ActionFragmentDict, EventFragmentDict
from wotpy.wot.dictionaries.link import LinkDict, FormDict
from wotpy.wot.dictionaries.schema import DataSchemaDict
from wotpy.wot.dictionaries.security import SecuritySchemeDict
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.dictionaries.version import VersioningDict
from wotpy.wot.enums import SecuritySchemeType, DataType


def test_link_dict():
    """Link dictionaries can be represented and serialized."""

    init = {
        "href": Faker().url(),
        "type": Faker().pystr()
    }

    link_dict = LinkDict(init)

    assert link_dict.to_dict().get("href") == init["href"]
    assert json.dumps(link_dict.to_dict())

    with pytest.raises(Exception):
        LinkDict({"type": Faker().pystr()})


def test_form_dict():
    """Form dictionaries can be represented and serialized."""

    init = {
        "href": Faker().url(),
        "type": Faker().pystr(),
        "security": [{"scheme": "nosec"}]
    }

    form_dict = FormDict(init)

    assert form_dict.content_type
    assert form_dict.to_dict().get("href") == init["href"]
    assert isinstance(form_dict.security[0], SecuritySchemeDict)
    assert form_dict.to_dict().get("security")[0]["scheme"] == init["security"][0]["scheme"]
    assert json.dumps(form_dict.to_dict())

    with pytest.raises(Exception):
        FormDict({"type": Faker().pystr()})


def test_property_fragment():
    """Property fragment dictionaries can be represented and serialized."""

    init = {
        "description": "Shows the current status of the lamp",
        "readOnly": True,
        "observable": False,
        "type": "string",
        "security": [{"scheme": "nosec"}],
        "forms": [{
            "href": "coaps://mylamp.example.com/status",
            "contentType": "application/json"
        }]
    }

    prop_fragment = PropertyFragmentDict(init)

    assert prop_fragment.read_only == init["readOnly"]
    assert prop_fragment.write_only is False
    assert prop_fragment.observable == init["observable"]
    assert isinstance(prop_fragment.data_schema, DataSchemaDict)
    assert prop_fragment.data_schema.type == init["type"]
    assert len(prop_fragment.forms) == len(init["forms"])
    assert prop_fragment.forms[0].href == init["forms"][0]["href"]
    assert prop_fragment.security[0].scheme == init["security"][0]["scheme"]
    assert json.dumps(prop_fragment.to_dict())

    with pytest.raises(Exception):
        PropertyFragmentDict({})


def test_action_fragment():
    """Action fragment dictionaries can be represented and serialized."""

    init = {
        "description": "Turn on or off the lamp",
        "forms": [{
            "href": "coaps://mylamp.example.com/toggle",
            "contentType": "application/json"
        }],
        "input": {
            "type": "string"
        },
        "output": {
            "description": "Fake output schema.",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "id": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["id"]
        }
    }

    action_fragment = ActionFragmentDict(init)

    assert action_fragment.description == init["description"]
    assert isinstance(action_fragment.input, DataSchemaDict)
    assert isinstance(action_fragment.output, DataSchemaDict)
    assert action_fragment.to_dict()["output"]["type"] == init["output"]["type"]
    assert json.dumps(action_fragment.to_dict())


def test_event_fragment():
    """Event fragment dictionaries can be represented and serialized."""

    init = {
        "description": "Lamp reaches a critical temperature (overheating)",
        "data": {"type": "string"},
        "forms": [{
            "href": "coaps://mylamp.example.com/oh",
            "contentType": "application/json"
        }],
        "uriVariables": {
            "p": {"type": "integer", "minimum": 0, "maximum": 16},
            "d": {"type": "integer", "minimum": 0, "maximum": 1}
        }
    }

    event_fragment = EventFragmentDict(init)

    assert event_fragment.description == init["description"]
    assert isinstance(event_fragment.data, DataSchemaDict)
    assert isinstance(next(six.itervalues(event_fragment.uri_variables)), DataSchemaDict)
    assert event_fragment.to_dict()["forms"][0]["href"] == init["forms"][0]["href"]
    assert json.dumps(event_fragment.to_dict())


THING_INIT = {
    "id": "urn:dev:wot:com:example:servient:lamp",
    "name": "MyLampThing",
    "description": "MyLampThing uses JSON-LD 1.1 serialization",
    "security": [{"scheme": "nosec"}],
    "version": {"instance": "1.2.1"},
    "properties": {
        "status": {
            "description": "Shows the current status of the lamp",
            "type": "string",
            "forms": [{
                "href": "coaps://mylamp.example.com/status"
            }]
        }
    },
    "actions": {
        "toggle": {
            "description": "Turn on or off the lamp",
            "forms": [{
                "href": "coaps://mylamp.example.com/toggle"
            }]
        }
    },
    "events": {
        "overheating": {
            "description": "Lamp reaches a critical temperature (overheating)",
            "data": {"type": "string"},
            "forms": [{
                "href": "coaps://mylamp.example.com/oh"
            }]
        }
    }
}


def test_thing_fragment():
    """Thing fragment dictionaries can be represented and serialized."""

    thing_fragment = ThingFragment(THING_INIT)

    assert thing_fragment.id == THING_INIT["id"]
    assert thing_fragment.name == THING_INIT["name"]
    assert thing_fragment.description == THING_INIT["description"]
    assert isinstance(next(six.itervalues(thing_fragment.properties)), PropertyFragmentDict)
    assert isinstance(next(six.itervalues(thing_fragment.actions)), ActionFragmentDict)
    assert isinstance(next(six.itervalues(thing_fragment.events)), EventFragmentDict)
    assert json.dumps(thing_fragment.to_dict())
    assert next(six.itervalues(thing_fragment.to_dict()["properties"]))["type"]
    assert thing_fragment.version.instance == THING_INIT["version"]["instance"]

    with pytest.raises(Exception):
        ThingFragment({})


def test_thing_fragment_setters():
    """Thing fragment properties can be set."""

    thing_fragment = ThingFragment(THING_INIT)

    with pytest.raises(AttributeError):
        thing_fragment.id = Faker().pystr()

    assert thing_fragment.name == THING_INIT["name"]

    name = Faker().pystr()

    # noinspection PyPropertyAccess
    thing_fragment.name = name

    assert thing_fragment.name != THING_INIT["name"]
    assert thing_fragment.name == name

    prop_fragment = PropertyFragmentDict(description=Faker().pystr(), type=DataType.NUMBER)
    props_updated = {Faker().pystr(): prop_fragment}

    # noinspection PyPropertyAccess
    thing_fragment.properties = props_updated

    assert next(six.itervalues(thing_fragment.properties)).description == prop_fragment.description

    security_updated = [SecuritySchemeDict(scheme=SecuritySchemeType.PSK)]

    # noinspection PyPropertyAccess
    thing_fragment.security = security_updated

    assert thing_fragment.security[0].scheme == security_updated[0].scheme

    version_updated = VersioningDict(instance=Faker().pystr())

    # noinspection PyPropertyAccess
    thing_fragment.version = version_updated

    assert thing_fragment.version.instance == version_updated.instance
