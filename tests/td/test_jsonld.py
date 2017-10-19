#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import random

import pytest
from jsonschema import ValidationError

from tests.td.resources import TD_EXAMPLE, INTERACTION_EXAMPLE
from tests.utils import random_dict_mess
from wotpy.td.enums import InteractionTypes
from wotpy.td.jsonld.interaction import JsonLDInteraction
from wotpy.td.jsonld.thing import JsonLDThingDescription


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

    def random_builder():
        return [
            random.random(),
            int(random.random()),
            [random.random() for _ in range(random.randint(1, 10))]
        ]

    td_dict = copy.deepcopy(TD_EXAMPLE)
    random_dict_mess(td_dict, random_builder=random_builder)

    with pytest.raises(ValidationError):
        thing_description_err = JsonLDThingDescription(doc=td_dict)
        thing_description_err.validate()


def test_interaction_properties():
    """Properties can be retrieved from Interaction objects."""

    interaction = JsonLDInteraction(INTERACTION_EXAMPLE)

    assert interaction.interaction_type == InteractionTypes.PROPERTY
    assert interaction.name == INTERACTION_EXAMPLE.get('name')
    assert len(interaction.link) == len(INTERACTION_EXAMPLE.get('link', []))


def test_thing_description_no_context():
    """Thing Descriptions without any context do not validate."""

    td_dict = copy.deepcopy(TD_EXAMPLE)

    jsonld_thing_descr = JsonLDThingDescription(doc=td_dict, validation=True)

    with pytest.raises(ValidationError):
        td_dict["@context"] = []
        jsonld_thing_descr.validate()
