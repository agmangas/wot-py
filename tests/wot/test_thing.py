#!/usr/bin/env python
# -*- coding: utf-8 -*-


import string
import uuid

# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
# noinspection PyPackageRequirements
from slugify import slugify

from wotpy.protocols.enums import Protocols
from wotpy.wot.td import ThingDescription
from wotpy.wot.form import Form
from wotpy.wot.interaction import Action
from wotpy.wot.thing import Thing


def test_unique_url_name():
    """URL names are always unique as long as the IDs are."""

    thing_id_base = uuid.uuid4().urn
    thing_ids = [thing_id_base]

    for ch in string.punctuation.replace("-", ""):
        thing_ids.append(thing_id_base.replace("-", ch))

    things = [Thing(id=item) for item in thing_ids]
    url_names = [item.url_name for item in things]

    assert len(url_names) == len(set(url_names))


def test_empty_thing_valid():
    """An empty Thing initialized by default has a valid JSON-LD serialization."""

    thing = Thing(id=uuid.uuid4().urn)
    json_td = ThingDescription.from_thing(thing)
    ThingDescription.validate(json_td.to_dict())


def test_interaction_invalid_name():
    """Invalid names for Interaction objects are rejected."""

    names_valid = [
        "safename",
        "safename02",
        "SafeName_03",
        "Safe_Name-04"
    ]

    names_invalid = [
        "!unsafename",
        "unsafe_name_ñ",
        "unsafe name",
        "?"
    ]

    thing = Thing(id=uuid.uuid4().urn)

    for name in names_valid:
        Action(thing=thing, name=name)

    for name in names_invalid:
        with pytest.raises(ValueError):
            Action(thing=thing, name=name)


def test_find_interaction():
    """Interactions may be retrieved by name on a Thing."""

    thing = Thing(id=uuid.uuid4().urn)

    interaction_01 = Action(thing=thing, name="my_interaction")
    interaction_02 = Action(thing=thing, name="AnotherInteraction")

    thing.add_interaction(interaction_01)
    thing.add_interaction(interaction_02)

    assert thing.find_interaction(interaction_01.name) is interaction_01
    assert thing.find_interaction(interaction_02.name) is interaction_02
    assert thing.find_interaction(slugify(interaction_01.name)) is interaction_01
    assert thing.find_interaction(slugify(interaction_02.name)) is interaction_02


def test_remove_interaction():
    """Interactions may be removed from a Thing by name."""

    thing = Thing(id=uuid.uuid4().urn)

    interaction_01 = Action(thing=thing, name="my_interaction")
    interaction_02 = Action(thing=thing, name="AnotherInteraction")
    interaction_03 = Action(thing=thing, name="YetAnother_interaction")

    thing.add_interaction(interaction_01)
    thing.add_interaction(interaction_02)
    thing.add_interaction(interaction_03)

    assert thing.find_interaction(interaction_01.name) is not None
    assert thing.find_interaction(interaction_02.name) is not None
    assert thing.find_interaction(interaction_03.name) is not None

    thing.remove_interaction(interaction_01.name)
    thing.remove_interaction(slugify(interaction_03.name))

    assert thing.find_interaction(interaction_01.name) is None
    assert thing.find_interaction(interaction_02.name) is not None
    assert thing.find_interaction(interaction_03.name) is None


def test_duplicated_interactions():
    """Duplicated Interactions are rejected on a Thing."""

    thing = Thing(id=uuid.uuid4().urn)

    interaction_01 = Action(thing=thing, name="my_interaction")
    interaction_02 = Action(thing=thing, name="AnotherInteraction")
    interaction_03 = Action(thing=thing, name="my_interaction")

    thing.add_interaction(interaction_01)
    thing.add_interaction(interaction_02)

    with pytest.raises(ValueError):
        thing.add_interaction(interaction_03)


def test_duplicated_forms():
    """Duplicated Forms are rejected on an Interaction."""

    thing = Thing(id=uuid.uuid4().urn)
    interaction = Action(thing=thing, name="my_interaction")
    thing.add_interaction(interaction)

    href_01 = "/href-01"
    href_02 = "/href-02"

    mtype_01 = "application/json"
    mtype_02 = "text/html"

    form_01 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, content_type=mtype_01)
    form_02 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, content_type=mtype_01)
    form_03 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, content_type=mtype_02)
    form_04 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, content_type=mtype_01)
    form_05 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, content_type=mtype_02)
    form_06 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, content_type=mtype_02)

    interaction.add_form(form_01)

    with pytest.raises(ValueError):
        interaction.add_form(form_02)

    interaction.add_form(form_03)
    interaction.add_form(form_04)
    interaction.add_form(form_05)

    with pytest.raises(ValueError):
        interaction.add_form(form_06)
