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
from wotpy.td.thing import Thing

SCHEMA_ORG_URL = "http://schema.org/"
SCHEMA_ORG_PREFIX = "schema"
SCHEMA_ORG_LOCATION = "location"
SCHEMA_ORG_ALTERNATE_NAME = "alternateName"
SCHEMA_ORG_LOCATION_KEY = "{}:{}".format(SCHEMA_ORG_PREFIX, SCHEMA_ORG_LOCATION)
SCHEMA_ORG_ALTERNATE_NAME_KEY = "{}:{}".format(SCHEMA_ORG_PREFIX, SCHEMA_ORG_ALTERNATE_NAME)


def test_jsonld_doc_from_thing():
    """JSON-LD document wrapper instances may be retrieved from
    Thing objects that are built using the Thing class interface."""

    fake = Faker()

    thing_location = fake.address()
    thing_name = fake.user_name()

    thing = Thing(name=thing_name)
    thing.semantic_metadata.add(key=SCHEMA_ORG_LOCATION_KEY, val=thing_location)
    thing.semantic_context.add(context_url=SCHEMA_ORG_URL, prefix=SCHEMA_ORG_PREFIX)

    prop_name = fake.user_name()
    prop_output_data = {"type": "number"}

    prop = Property(thing=thing, name=prop_name, output_data=prop_output_data, writable=True)

    form_href_01 = "/prop-01"
    form_media_type_01 = "application/json"

    form_href_02 = "/prop-02"
    form_media_type_02 = "application/json"

    form_01 = Form(interaction=prop, protocol=Protocols.HTTP, href=form_href_01, media_type=form_media_type_01)
    form_02 = Form(interaction=prop, protocol=Protocols.HTTP, href=form_href_02, media_type=form_media_type_02)

    prop.add_form(form_01)
    prop.add_form(form_02)
    thing.add_interaction(prop)

    jsonld_thing_descr = thing.to_jsonld_thing_description()
    jsonld_property = jsonld_thing_descr.interaction[0]
    jsonld_form_01 = jsonld_property.form[0]

    assert len(jsonld_thing_descr.interaction) == 1
    assert len(jsonld_property.form) == 2
    assert jsonld_thing_descr.name == thing_name
    assert jsonld_property.output_data["type"] == prop_output_data["type"]
    assert jsonld_form_01.doc.get("href") == form_href_01
    assert jsonld_property.doc.get(SCHEMA_ORG_LOCATION_KEY, None) is None

    prop_location = fake.address()

    prop_after = thing.interactions[0]
    prop_after.semantic_metadata.add(key=SCHEMA_ORG_LOCATION_KEY, val=prop_location)

    jsonld_thing_descr_after = thing.to_jsonld_thing_description()
    jsonld_property_after = jsonld_thing_descr_after.interaction[0]

    assert jsonld_thing_descr_after.name == thing_name
    assert jsonld_property_after.doc.get(SCHEMA_ORG_LOCATION_KEY, None) == prop_location


def test_semantic_metadata():
    """Semantic metadata items can be added to all TD hierarchy objects."""

    fake = Faker()

    thing = Thing(name=fake.user_name())
    proprty = Property(thing=thing, name=fake.user_name(), output_data={"type": "number"})
    form = Form(interaction=proprty, protocol=Protocols.HTTP, href="/prop", media_type="application/json")

    proprty.add_form(form)
    thing.add_interaction(proprty)

    thing_location = fake.address()
    prop_alt_name = fake.user_name()
    form_alt_name = fake.user_name()

    thing.semantic_metadata.add(SCHEMA_ORG_LOCATION_KEY, thing_location)
    proprty.semantic_metadata.add(SCHEMA_ORG_ALTERNATE_NAME_KEY, prop_alt_name)
    form.semantic_metadata.add(SCHEMA_ORG_ALTERNATE_NAME_KEY, form_alt_name)

    jsonld_td = thing.to_jsonld_thing_description()
    jsonld_interaction = jsonld_td.interaction[0]
    jsonld_form = jsonld_td.interaction[0].form[0]

    assert jsonld_td.metadata.get(SCHEMA_ORG_LOCATION_KEY) == thing_location
    assert jsonld_interaction.metadata.get(SCHEMA_ORG_ALTERNATE_NAME_KEY) == prop_alt_name
    assert jsonld_interaction.metadata.get(SCHEMA_ORG_LOCATION_KEY, None) is None
    assert jsonld_form.metadata.get(SCHEMA_ORG_ALTERNATE_NAME_KEY) == form_alt_name


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
    jsonld_td = thing.to_jsonld_thing_description()
    jsonld_td.validate()


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

    media_type_01 = "application/json"
    media_type_02 = "text/html"

    form_01 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, media_type=media_type_01)
    form_02 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, media_type=media_type_01)
    form_03 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_01, media_type=media_type_02)
    form_04 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, media_type=media_type_01)
    form_05 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, media_type=media_type_02)
    form_06 = Form(interaction=interaction, protocol=Protocols.HTTP, href=href_02, media_type=media_type_02)

    interaction.add_form(form_01)

    with pytest.raises(ValueError):
        interaction.add_form(form_02)

    interaction.add_form(form_03)
    interaction.add_form(form_04)
    interaction.add_form(form_05)

    with pytest.raises(ValueError):
        interaction.add_form(form_06)
