#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import pytest
from faker import Faker
from jsonschema import ValidationError

from tests.td_examples import TD_EXAMPLE
from wotpy.td.enums import InteractionTypes
from wotpy.td.jsonld.interaction import JsonLDInteraction
from wotpy.td.jsonld.thing import JsonLDThingDescription
from wotpy.td.constants import WOT_TD_CONTEXT_URL


def test_thing_description_validate():
    """Example Thing Description from W3C GitHub page validates correctly."""

    thing_description = JsonLDThingDescription(doc=TD_EXAMPLE)
    thing_description.validate()


def test_thing_description_properties():
    """Properties can be retrieved from Thing Description objects."""

    thing_description = JsonLDThingDescription(doc=TD_EXAMPLE)

    assert thing_description.name == TD_EXAMPLE.get('name')
    assert thing_description.base == TD_EXAMPLE.get('base')
    assert len(thing_description.interaction) == len(TD_EXAMPLE.get('interaction', []))


def test_thing_description_validate_err():
    """An erroneous Thing Description raises error on validation."""

    fake = Faker()

    td_err_01 = copy.deepcopy(TD_EXAMPLE)
    td_err_01["interaction"] = fake.pydict()

    with pytest.raises(ValidationError):
        jsonld_td_err = JsonLDThingDescription(doc=td_err_01)
        jsonld_td_err.validate()

    td_err_02 = copy.deepcopy(TD_EXAMPLE)
    td_err_02.pop("name")

    with pytest.raises(ValidationError):
        jsonld_td_err = JsonLDThingDescription(doc=td_err_02)
        jsonld_td_err.validate()

    td_err_03 = copy.deepcopy(TD_EXAMPLE)
    td_err_03["interaction"][0].pop("@type")

    with pytest.raises(ValidationError):
        jsonld_td_err = JsonLDThingDescription(doc=td_err_03)
        jsonld_td_err.validate()


def test_interaction_properties():
    """Properties can be retrieved from Interaction objects."""

    interaction_doc = TD_EXAMPLE["interaction"][0]

    jsonld_td = JsonLDThingDescription(TD_EXAMPLE)
    jsonld_interaction = JsonLDInteraction(interaction_doc, jsonld_td)

    assert jsonld_interaction.interaction_type == InteractionTypes.PROPERTY
    assert jsonld_interaction.name == interaction_doc.get('name')
    assert len(jsonld_interaction.form) == len(interaction_doc.get('form', []))


def test_thing_description_no_context():
    """Thing Descriptions without the required context do not validate."""

    td_dict = copy.deepcopy(TD_EXAMPLE)

    jsonld_thing_descr = JsonLDThingDescription(doc=td_dict)

    td_dict["@context"] = []

    with pytest.raises(ValidationError):
        jsonld_thing_descr.validate()

    td_dict["@context"] = [{"schema": "http://schema.org/"}]

    with pytest.raises(ValidationError):
        jsonld_thing_descr.validate()

    td_dict["@context"] = [WOT_TD_CONTEXT_URL, {"schema": "http://schema.org/"}]
    jsonld_thing_descr.validate()
