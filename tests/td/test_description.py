#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import uuid

# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from wotpy.protocols.enums import Protocols
from wotpy.td.description import JSONThingDescription
from wotpy.td.form import Form
from wotpy.td.interaction import Action
from wotpy.td.thing import Thing
from wotpy.td.validation import InvalidDescription


def test_validate():
    """Example TD from the W3C Thing Description page validates correctly."""

    JSONThingDescription.validate(doc=TD_EXAMPLE)


def test_validate_err():
    """An erroneous Thing Description raises error on validation."""

    update_funcs = [
        lambda x: x.update({"properties": [1, 2, 3]}) or x,
        lambda x: x.update({"actions": "hello-interactions"}) or x,
        lambda x: x.update({"events": {"overheating": {"forms": 0.5}}}) or x,
        lambda x: x.update({"id": "this is not an URI"}) or x,
        lambda x: x.update({"events": {"Invalid Name": {}}}) or x,
        lambda x: x.update({"events": {100: {"label": "Invalid Name"}}}) or x
    ]

    for update_func in update_funcs:
        td_err = update_func(copy.deepcopy(TD_EXAMPLE))

        with pytest.raises(InvalidDescription):
            JSONThingDescription.validate(doc=td_err)


def test_from_thing():
    """Thing instances can be serialized to JSON format."""

    fake = Faker()

    thing_id = uuid.uuid4().urn
    action_id = uuid.uuid4().hex
    form_href = fake.url()

    thing = Thing(id=thing_id)
    action = Action(thing=thing, id=action_id)
    form = Form(interaction=action, protocol=Protocols.HTTP, href=form_href)

    action.add_form(form)
    thing.add_interaction(action)

    json_td = JSONThingDescription.from_thing(thing)
    td_dict = json_td.to_dict()

    assert td_dict["id"] == thing_id
    assert len(td_dict["properties"]) == 0
    assert len(td_dict["actions"]) == 1
    assert len(td_dict["actions"][action_id]["forms"]) == 1
    assert td_dict["actions"][action_id]["forms"][0]["href"] == form_href


def test_build_thing():
    """Thing instances can be built from JSON TD instances."""

    json_td = JSONThingDescription(TD_EXAMPLE)
    thing = json_td.build_thing()
    td_dict = json_td.to_dict()

    def assert_same_keys(dict_a, dict_b):
        assert sorted(list(dict_a.keys())) == sorted(list(dict_b.keys()))

    assert thing.id == td_dict.get("id")
    assert thing.label == td_dict.get("label")
    assert thing.description == td_dict.get("description")
    assert_same_keys(thing.properties, td_dict.get("properties", {}))
    assert_same_keys(thing.actions, td_dict.get("actions", {}))
    assert_same_keys(thing.events, td_dict.get("events", {}))
