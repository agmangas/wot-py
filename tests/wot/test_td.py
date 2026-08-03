#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

import copy
import uuid

import pytest
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from wotpy.protocols.enums import Protocols
from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.td import ThingDescription
from wotpy.wot.form import Form
from wotpy.wot.interaction import Action, Property, Event
from wotpy.wot.thing import Thing
from wotpy.wot.validation import InvalidDescription


def test_validate():
    """Example TD from the W3C Thing Description page validates correctly."""

    ThingDescription.validate(doc=TD_EXAMPLE)


def test_validate_err():
    """An erroneous Thing Description raises error on validation."""

    update_funcs = [
        lambda x: x.update({"properties": [1, 2, 3]}) or x,
        lambda x: x.update({"actions": "hello-interactions"}) or x,
        lambda x: x.update({"events": {"overheating": {"forms": 0.5}}}) or x,
    ]

    for update_func in update_funcs:
        td_err = update_func(copy.deepcopy(TD_EXAMPLE))

        with pytest.raises(InvalidDescription):
            ThingDescription.validate(doc=td_err)


def test_from_dict():
    """ThingDescription objects can be built from TD documents in dict format."""

    td = ThingDescription(TD_EXAMPLE)

    assert td.id == TD_EXAMPLE.get("id")
    assert td.title == TD_EXAMPLE.get("title")
    assert td.description == TD_EXAMPLE.get("description")


def test_from_thing():
    """ThingDescription objects can be built from Thing objects."""

    fake = Faker()

    thing_id = uuid.uuid4().urn
    action_id = uuid.uuid4().hex
    prop_id = uuid.uuid4().hex
    event_id = uuid.uuid4().hex
    action_form_href = fake.url()
    prop_form_href = fake.url()
    event_form_href = fake.url()

    thing_fragment = ThingFragment({
        "@context": [
            WOT_TD_CONTEXT_URL_V1_1,
        ],
        "id": thing_id,
        "title": uuid.uuid4().hex,
        "securityDefinitions": {
            "nosec_sc":{
                "scheme":"nosec"
            }
        },
        "security": "nosec_sc"
    })
    thing = Thing(thing_fragment=thing_fragment)

    action = Action(thing=thing, name=action_id)
    action_form = Form(interaction=action, protocol=Protocols.HTTP, href=action_form_href)
    action.add_form(action_form)
    thing.add_interaction(action)

    prop = Property(thing=thing, name=prop_id, type="string")
    prop_form = Form(interaction=prop, protocol=Protocols.HTTP, href=prop_form_href)
    prop.add_form(prop_form)
    thing.add_interaction(prop)

    event = Event(thing=thing, name=event_id)
    thing.add_interaction(event)

    json_td = ThingDescription.from_thing(thing)
    td_dict = json_td.to_dict()

    assert td_dict["id"] == thing.id
    assert td_dict["title"] == thing.title
    assert len(td_dict["properties"]) == 1
    assert len(td_dict["actions"]) == 1
    assert len(td_dict["events"]) == 1
    assert len(td_dict["actions"][action_id]["forms"]) == 1
    assert len(td_dict["properties"][prop_id]["forms"]) == 1
    assert td_dict["actions"][action_id]["forms"][0]["href"] == action_form_href
    assert td_dict["properties"][prop_id]["forms"][0]["href"] == prop_form_href


def test_build_thing():
    """Thing objects can be built from ThingDescription objects."""

    json_td = ThingDescription(TD_EXAMPLE)
    thing = json_td.build_thing()
    td_dict = json_td.to_dict()

    def assert_same_keys(dict_a, dict_b):
        assert sorted(list(dict_a.keys())) == sorted(list(dict_b.keys()))

    assert thing.id == td_dict.get("id")
    assert thing.title == td_dict.get("title")
    assert thing.description == td_dict.get("description")
    assert_same_keys(thing.properties, td_dict.get("properties", {}))
    assert_same_keys(thing.actions, td_dict.get("actions", {}))
    assert_same_keys(thing.events, td_dict.get("events", {}))
