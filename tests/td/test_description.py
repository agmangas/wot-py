#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import pytest

from tests.td_examples import TD_EXAMPLE
from wotpy.td.description import JSONThingDescription
from wotpy.td.validation import InvalidDescription


def test_thing_description_validate():
    """Example Thing Description from W3C GitHub page validates correctly."""

    JSONThingDescription.validate(doc=TD_EXAMPLE)


def test_thing_description_validate_err():
    """An erroneous Thing Description raises error on validation."""

    td_err_01 = copy.deepcopy(TD_EXAMPLE)
    td_err_01["properties"] = [1, 2, 3]

    with pytest.raises(InvalidDescription):
        JSONThingDescription.validate(doc=td_err_01)

    td_err_02 = copy.deepcopy(TD_EXAMPLE)
    td_err_02["actions"] = "hello-interactions"

    with pytest.raises(InvalidDescription):
        JSONThingDescription.validate(doc=td_err_02)

    td_err_03 = copy.deepcopy(TD_EXAMPLE)
    td_err_03["events"] = {
        "overheating": {
            "forms": 0.5
        }
    }

    with pytest.raises(InvalidDescription):
        JSONThingDescription.validate(doc=td_err_03)

    td_err_04 = copy.deepcopy(TD_EXAMPLE)
    td_err_04["id"] = "this is not a URI"

    with pytest.raises(InvalidDescription):
        JSONThingDescription.validate(doc=td_err_04)
