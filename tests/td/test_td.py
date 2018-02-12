#!/usr/bin/env python
# -*- coding: utf-8 -*-

from faker import Faker

from wotpy.protocols.enums import Protocols
from wotpy.td.interaction import Property
from wotpy.td.form import Form
from wotpy.td.thing import Thing

SCHEMA_ORG_URL = "http://schema.org/"
SCHEMA_ORG_PREFIX = "schema"
SCHEMA_ORG_LOCATION = "location"
SCHEMA_ORG_LOCATION_KEY = "{}:{}".format(SCHEMA_ORG_PREFIX, SCHEMA_ORG_LOCATION)


def test_jsonld_doc_from_thing():
    """JSON-LD document wrapper instances may be retrieved from
    Thing objects that are built using the Thing class interface."""

    fake = Faker()

    thing_location = fake.address()
    thing_name = fake.user_name()

    thing = Thing(name=thing_name, SCHEMA_ORG_LOCATION_KEY=thing_location)
    thing.add_context(context_url=SCHEMA_ORG_URL, context_prefix=SCHEMA_ORG_PREFIX)

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

    prop_after = thing.interaction[0]
    prop_after.metadata.update({SCHEMA_ORG_LOCATION_KEY: prop_location})

    jsonld_thing_descr_after = thing.to_jsonld_thing_description()
    jsonld_property_after = jsonld_thing_descr_after.interaction[0]

    assert jsonld_thing_descr_after.name == thing_name
    assert jsonld_property_after.doc.get(SCHEMA_ORG_LOCATION_KEY, None) == prop_location


def test_thing_equality():
    """Things with the same name are equal."""

    fake = Faker()

    name_01 = fake.user_name()
    name_02 = fake.user_name()
    location = fake.address()

    thing_01 = Thing(name=name_01, SCHEMA_ORG_LOCATION_KEY=location)
    thing_02 = Thing(name=name_01)
    thing_03 = Thing(name=name_02)

    assert thing_01 == thing_02
    assert thing_01 != thing_03
    assert thing_01 in [thing_02]
    assert thing_01 not in [thing_03]


def test_interaction_equality():
    """Interactions with the same name are equal."""

    fake = Faker()

    name_01 = fake.user_name()
    name_02 = fake.user_name()
    location = fake.address()

    interaction_01 = Thing(name=name_01)
    interaction_01.metadata.update({SCHEMA_ORG_LOCATION_KEY: location})
    interaction_02 = Thing(name=name_01)
    interaction_03 = Thing(name=name_02)

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


def test_thing_duplicated_contexts():
    """It is not possible to add duplicated contexts to Things."""

    fake = Faker()

    ctx_url_01 = fake.url()
    ctx_url_02 = fake.url()
    ctx_url_03 = fake.url()
    ctx_prefix_01 = fake.user_name()
    ctx_prefix_02 = fake.user_name()
    name = fake.user_name()

    thing = Thing(name=name)

    base_len = len(thing.context)

    thing.add_context(context_url=ctx_url_01)
    assert len(thing.context) == base_len + 1

    thing.add_context(context_url=ctx_url_01)
    assert len(thing.context) == base_len + 1

    thing.add_context(context_url=ctx_url_02)
    assert len(thing.context) == base_len + 2

    thing.add_context(context_url=ctx_url_02, context_prefix=ctx_prefix_01)
    assert len(thing.context) == base_len + 3

    thing.add_context(context_url=ctx_url_03, context_prefix=ctx_prefix_01)
    assert len(thing.context) == base_len + 3

    thing.add_context(context_url=ctx_url_03, context_prefix=ctx_prefix_02)
    assert len(thing.context) == base_len + 4

    thing.add_context(context_url=ctx_url_03)
    assert len(thing.context) == base_len + 5
