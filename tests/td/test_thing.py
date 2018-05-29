#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
from slugify import slugify

from wotpy.protocols.enums import Protocols
from wotpy.td.form import Form
from wotpy.td.interaction import Action
from wotpy.td.description import JSONThingDescription
from wotpy.td.thing import Thing


def test_empty_thing_valid():
    """An empty Thing initialized by default has a valid JSON-LD serialization."""

    thing = Thing(id="urn:mything")
    JSONThingDescription.from_thing(thing)


def test_interaction_unsafe_names():
    """Unsafe names for Interaction objects are rejected."""

    names_safe = [
        "safename",
        "safename02",
        "SafeName_03",
        "Safe_Name-04"
    ]

    names_unsafe = [
        "!unsafename",
        "unsafe_name_ñ",
        "unsafe name",
        "?"
    ]

    thing = Thing(id="urn:mything")

    for name in names_safe:
        Action(thing=thing, id=name)

    for name in names_unsafe:
        with pytest.raises(ValueError):
            Action(thing=thing, id=name)


def test_find_interaction():
    """Interactions may be retrieved by name on a Thing."""

    thing = Thing(id="urn:mything")

    interaction_01 = Action(thing=thing, id="my_interaction")
    interaction_02 = Action(thing=thing, id="AnotherInteraction")

    thing.add_interaction(interaction_01)
    thing.add_interaction(interaction_02)

    assert thing.find_interaction(interaction_01.name) is interaction_01
    assert thing.find_interaction(interaction_02.name) is interaction_02
    assert thing.find_interaction(slugify(interaction_01.name)) is interaction_01
    assert thing.find_interaction(slugify(interaction_02.name)) is interaction_02


def test_remove_interaction():
    """Interactions may be removed from a Thing by name."""

    thing = Thing(id="urn:mything")

    interaction_01 = Action(thing=thing, id="my_interaction")
    interaction_02 = Action(thing=thing, id="AnotherInteraction")
    interaction_03 = Action(thing=thing, id="YetAnother_interaction")

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

    thing = Thing(id="urn:mything")

    interaction_01 = Action(thing=thing, id="my_interaction")
    interaction_02 = Action(thing=thing, id="AnotherInteraction")
    interaction_03 = Action(thing=thing, id="my_interaction")

    thing.add_interaction(interaction_01)
    thing.add_interaction(interaction_02)

    with pytest.raises(ValueError):
        thing.add_interaction(interaction_03)


def test_duplicated_forms():
    """Duplicated Forms are rejected on an Interaction."""

    thing = Thing(id="urn:mything")
    interaction = Action(thing=thing, id="my_interaction")
    thing.add_interaction(interaction)

    href_01 = "/href-01"
    href_02 = "/href-02"

    mtype_01 = "application/json"
    mtype_02 = "text/html"

    form_01 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, media_type=mtype_01)
    form_02 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, media_type=mtype_01)
    form_03 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, media_type=mtype_02)
    form_04 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, media_type=mtype_01)
    form_05 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, media_type=mtype_02)
    form_06 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, media_type=mtype_02)

    interaction.add_form(form_01)

    with pytest.raises(ValueError):
        interaction.add_form(form_02)

    interaction.add_form(form_03)
    interaction.add_form(form_04)
    interaction.add_form(form_05)

    with pytest.raises(ValueError):
        interaction.add_form(form_06)
