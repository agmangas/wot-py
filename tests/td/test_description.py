#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import pytest
from faker import Faker

from tests.td_examples import TD_EXAMPLE
from wotpy.td.constants import WOT_TD_CONTEXT_URL
from wotpy.td.jsonld.description import ThingDescription, InvalidDescription


def test_thing_description_validate():
    """Example Thing Description from W3C GitHub page validates correctly."""

    ThingDescription.validate(doc=TD_EXAMPLE)


def test_thing_description_validate_err():
    """An erroneous Thing Description raises error on validation."""

    fake = Faker()

    td_err_01 = copy.deepcopy(TD_EXAMPLE)
    td_err_01["interaction"] = fake.pydict()

    with pytest.raises(InvalidDescription):
        ThingDescription.validate(doc=td_err_01)

    td_err_02 = copy.deepcopy(TD_EXAMPLE)
    td_err_02.pop("name")

    with pytest.raises(InvalidDescription):
        ThingDescription.validate(doc=td_err_02)

    td_err_03 = copy.deepcopy(TD_EXAMPLE)
    td_err_03["interaction"][0].pop("@type")

    with pytest.raises(InvalidDescription):
        ThingDescription.validate(doc=td_err_03)


def test_thing_description_no_context():
    """Thing Descriptions without the required context do not validate."""

    td_doc = copy.deepcopy(TD_EXAMPLE)

    ThingDescription.validate(doc=td_doc)

    td_doc["@context"] = []

    with pytest.raises(InvalidDescription):
        ThingDescription.validate(doc=td_doc)

    td_doc["@context"] = [{"schema": "http://schema.org/"}]

    with pytest.raises(InvalidDescription):
        ThingDescription.validate(doc=td_doc)

    td_doc["@context"] = [WOT_TD_CONTEXT_URL, {"schema": "http://schema.org/"}]

    ThingDescription.validate(doc=td_doc)
