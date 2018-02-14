#!/usr/bin/env python
# -*- coding: utf-8 -*-

from faker import Faker

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

    property = Property(thing=thing, name=fake.user_name(), output_data={"type": "number"})
    action = Action(thing=thing, name=fake.user_name())
    event = Event(thing=thing, name=fake.user_name(), output_data={"type": "string"})

    assert InteractionTypes.PROPERTY in property.types
    assert InteractionTypes.ACTION in action.types
    assert InteractionTypes.EVENT in event.types


def test_empty_thing_valid():
    """An empty Thing initialized by default has a valid JSON-LD serialization."""

    fake = Faker()

    thing = Thing(name=fake.user_name())

    jsonld_td = thing.to_jsonld_thing_description()
    jsonld_td.validate()


def test_thing_equality():
    """Things with the same name are equal."""

    fake = Faker()

    name_01 = fake.user_name()
    name_02 = fake.user_name()
    location = fake.address()

    thing_01 = Thing(name=name_01)
    thing_01.semantic_metadata.add(key=SCHEMA_ORG_LOCATION_KEY, val=location)
    thing_02 = Thing(name=name_01)
    thing_03 = Thing(name=name_02)

    assert thing_01 == thing_02
    assert thing_01 != thing_03
    assert thing_01 in [thing_02]
    assert thing_01 not in [thing_03]


def test_interaction_equality():
    """Interactions with the same name are equal."""

    fake = Faker()

    name_thing = fake.user_name()
    name_01 = fake.user_name()
    name_02 = fake.user_name()

    thing = Thing(name=name_thing)
    interaction_01 = Action(thing=thing, name=name_01)
    interaction_02 = Action(thing=thing, name=name_01)
    interaction_03 = Action(thing=thing, name=name_02)

    assert interaction_01 == interaction_02
    assert interaction_01 != interaction_03
    assert interaction_01 in [interaction_02]
    assert interaction_01 not in [interaction_03]


def test_form_equality():
    """Forms with the same media type and href are equal."""

    fake = Faker()

    thing_name = fake.user_name()
    href_01 = fake.url()
    href_02 = fake.url()
    media_type_01 = "application/json"
    media_type_02 = "text/html"
    prop_name = fake.user_name()
    prop_output_data = {"type": "number"}

    thing = Thing(name=thing_name)
    prop = Property(thing=thing, name=prop_name, output_data=prop_output_data)

    form_01 = Form(interaction=prop, protocol=Protocols.HTTP, href=href_01, media_type=media_type_01)
    form_02 = Form(interaction=prop, protocol=Protocols.HTTP, href=href_01, media_type=media_type_01)
    form_03 = Form(interaction=prop, protocol=Protocols.HTTP, href=href_01, media_type=media_type_02)
    form_04 = Form(interaction=prop, protocol=Protocols.HTTP, href=href_02, media_type=media_type_01)

    assert form_01 == form_02
    assert form_01 != form_03
    assert form_01 != form_04
    assert form_01 in [form_02]
    assert form_01 not in [form_03, form_04]
