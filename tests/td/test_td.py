#!/usr/bin/env python
# -*- coding: utf-8 -*-

from faker import Faker

from wotpy.td.interaction import Property
from wotpy.td.link import Link
from wotpy.td.thing import Thing

SCHEMA_ORG_URL = "http://schema.org/"
SCHEMA_ORG_PREFIX = "schema"
SCHEMA_ORG_LOCATION = "location"


def test_jsonld_doc_from_thing():
    """JSON-LD document wrapper instances may be retrieved from
    Thing objects that are built using the Thing class interface."""

    fake = Faker()

    thing_location = fake.address()
    thing_name = fake.user_name()
    schema_location_key = "{}:{}".format(SCHEMA_ORG_PREFIX, SCHEMA_ORG_LOCATION)

    thing = Thing(name=thing_name)
    thing.add_context(context_url=SCHEMA_ORG_URL, context_prefix=SCHEMA_ORG_PREFIX)
    thing.add_meta(key=schema_location_key, val=thing_location)

    prop_name = fake.user_name()
    prop_output_data = {"type": "number"}

    prop = Property(name=prop_name, output_data=prop_output_data, writable=True)

    link_href_01 = "/prop-01"
    link_media_type_01 = "application/json"

    link_href_02 = "/prop-02"
    link_media_type_02 = "application/json"

    link_01 = Link(href=link_href_01, media_type=link_media_type_01)
    link_02 = Link(href=link_href_02, media_type=link_media_type_02)

    prop.add_link(link_01)
    prop.add_link(link_02)
    thing.add_interaction(prop)

    jsonld_thing_descr = thing.to_jsonld_thing_description()
    jsonld_property = jsonld_thing_descr.interaction[0]
    jsonld_link_01 = jsonld_property.link[0]

    assert len(jsonld_thing_descr.interaction) == 1
    assert len(jsonld_property.link) == 2
    assert jsonld_thing_descr.name == thing_name
    assert jsonld_property.output_data["type"] == prop_output_data["type"]
    assert jsonld_link_01.href == link_href_01
    assert jsonld_property.doc.get(schema_location_key, None) is None

    prop_location = fake.address()

    prop_after = thing.interaction[0]
    prop_after.add_meta(key=schema_location_key, val=prop_location)

    jsonld_thing_descr_after = thing.to_jsonld_thing_description()
    jsonld_property_after = jsonld_thing_descr_after.interaction[0]

    assert jsonld_thing_descr_after.name == thing_name
    assert jsonld_property_after.doc.get(schema_location_key, None) == prop_location
