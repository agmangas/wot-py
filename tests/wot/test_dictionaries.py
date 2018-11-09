#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json

import pytest
import six
from faker import Faker

from wotpy.wot.dictionaries.interaction import PropertyFragment, ActionFragment, EventFragment
from wotpy.wot.dictionaries.link import LinkDict, FormDict
from wotpy.wot.dictionaries.schema import DataSchema
from wotpy.wot.dictionaries.security import SecuritySchemeDict
from wotpy.wot.dictionaries.thing import ThingFragment


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

    prop_fragment = PropertyFragment(init)

    assert prop_fragment.read_only == init["readOnly"]
    assert prop_fragment.write_only is False
    assert prop_fragment.observable == init["observable"]
    assert isinstance(prop_fragment.data_schema, DataSchema)
    assert prop_fragment.data_schema.type == init["type"]
    assert len(prop_fragment.forms) == len(init["forms"])
    assert prop_fragment.forms[0].href == init["forms"][0]["href"]
    assert prop_fragment.security[0].scheme == init["security"][0]["scheme"]
    assert json.dumps(prop_fragment.to_dict())

    with pytest.raises(Exception):
        PropertyFragment({})


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

    action_fragment = ActionFragment(init)

    assert action_fragment.description == init["description"]
    assert isinstance(action_fragment.input, DataSchema)
    assert isinstance(action_fragment.output, DataSchema)
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

    event_fragment = EventFragment(init)

    assert event_fragment.description == init["description"]
    assert isinstance(event_fragment.data, DataSchema)
    assert isinstance(next(six.itervalues(event_fragment.uri_variables)), DataSchema)
    assert event_fragment.to_dict()["forms"][0]["href"] == init["forms"][0]["href"]
    assert json.dumps(event_fragment.to_dict())


def test_thing_fragment():
    """Thing fragment dictionaries can be represented and serialized."""

    init = {
        "id": "urn:dev:wot:com:example:servient:lamp",
        "name": "MyLampThing",
        "description": "MyLampThing uses JSON-LD 1.1 serialization",
        "security": [{"scheme": "nosec"}],
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

    thing_fragment = ThingFragment(init)

    assert thing_fragment.id == init["id"]
    assert thing_fragment.name == init["name"]
    assert thing_fragment.description == init["description"]
    assert isinstance(next(six.itervalues(thing_fragment.properties)), PropertyFragment)
    assert isinstance(next(six.itervalues(thing_fragment.actions)), ActionFragment)
    assert isinstance(next(six.itervalues(thing_fragment.events)), EventFragment)
    assert json.dumps(thing_fragment.to_dict())
    assert next(six.itervalues(thing_fragment.to_dict()["properties"]))["type"]

    with pytest.raises(Exception):
        ThingFragment({})
