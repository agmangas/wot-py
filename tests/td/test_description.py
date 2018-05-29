#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

import pytest

from tests.td_examples import TD_EXAMPLE
from wotpy.td.description import JSONThingDescription
from wotpy.td.validation import InvalidDescription


def test_thing_description_validate():
    """Example TD from the W3C Thing Description page validates correctly."""

    JSONThingDescription.validate(doc=TD_EXAMPLE)


def test_thing_description_validate_err():
    """An erroneous Thing Description raises error on validation."""

    update_funcs = [
        lambda x: x.update({"properties": [1, 2, 3]}) or x,
        lambda x: x.update({"actions": "hello-interactions"}) or x,
        lambda x: x.update({"events": {"overheating": {"forms": 0.5}}}) or x,
        lambda x: x.update({"id": "this is not an URI"}) or x,
        lambda x: x.update({"events": {"Invalid Name": {}}}) or x,
        lambda x: x.update({"events": {100: {"label": "Invalid Name"}}}) or x
    ]

    for update_func in update_funcs:
        td_err = update_func(copy.deepcopy(TD_EXAMPLE))

        with pytest.raises(InvalidDescription):
            JSONThingDescription.validate(doc=td_err)
