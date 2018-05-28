#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
from faker import Faker
# noinspection PyPackageRequirements
from slugify import slugify

from wotpy.protocols.enums import Protocols
from wotpy.td.enums import InteractionTypes
from wotpy.td.form import Form
from wotpy.td.interaction import Property, Action, Event
from wotpy.td.jsonld.description import ThingDescription
from wotpy.td.thing import Thing

SCHEMA_ORG_URL = "http://schema.org/"
SCHEMA_ORG_PREFIX = "schema"
SCHEMA_ORG_LOCATION = "location"
SCHEMA_ORG_ALTERNATE_NAME = "alternateName"
SCHEMA_ORG_LOCATION_KEY = "{}:{}".format(SCHEMA_ORG_PREFIX, SCHEMA_ORG_LOCATION)
SCHEMA_ORG_ALTERNATE_NAME_KEY = "{}:{}".format(SCHEMA_ORG_PREFIX, SCHEMA_ORG_ALTERNATE_NAME)


def test_interaction_types():
    """Interaction objects contain the appropriate types by default."""

    fake = Faker()

    thing = Thing(name=fake.user_name())

    proprty = Property(thing=thing, name=fake.user_name(), output_data={"type": "number"})
    action = Action(thing=thing, name=fake.user_name())
    event = Event(thing=thing, name=fake.user_name(), output_data={"type": "string"})

    assert InteractionTypes.PROPERTY in proprty.types
    assert InteractionTypes.ACTION in action.types
    assert InteractionTypes.EVENT in event.types


def test_empty_thing_valid():
    """An empty Thing initialized by default has a valid JSON-LD serialization."""

    thing = Thing(name="MyThing")
    ThingDescription.validate(thing.to_jsonld_dict())


def test_unsafe_names():
    """Unsafe names for Thing or Interaction objects are rejected."""

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

    for name in names_safe:
        thing = Thing(name=name)
        Action(thing=thing, name=name)

    thing_name = names_safe[0]

    for name in names_unsafe:
        with pytest.raises(ValueError):
            Thing(name=name)

        thing = Thing(name=thing_name)

        with pytest.raises(ValueError):
            Action(thing=thing, name=name)


def test_find_interaction():
    """Interactions may be retrieved by name on a Thing."""

    thing = Thing(name="my_thing")

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

    thing = Thing(name="my_thing")

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

    thing = Thing(name="my_thing")

    interaction_01 = Action(thing=thing, name="my_interaction")
    interaction_02 = Action(thing=thing, name="AnotherInteraction")
    interaction_03 = Action(thing=thing, name="my_interaction")
    interaction_04 = Action(thing=thing, name="My-Interaction")

    thing.add_interaction(interaction_01)
    thing.add_interaction(interaction_02)

    with pytest.raises(ValueError):
        thing.add_interaction(interaction_03)

    with pytest.raises(ValueError):
        thing.add_interaction(interaction_04)


def test_duplicated_forms():
    """Duplicated Forms are rejected on an Interaction."""

    thing = Thing(name="my_thing")
    interaction = Action(thing=thing, name="my_interaction")
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
