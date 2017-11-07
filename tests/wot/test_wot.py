#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
from faker import Faker

from wotpy.wot.dictionaries import ThingInit
from wotpy.wot.servient import Servient
from wotpy.wot.wot import WoT
from tests.td_examples import TD_EXAMPLE


def test_expose():
    """Things can be exposed using the WoT entrypoint."""

    fake = Faker()

    name_01 = fake.pystr()
    name_02 = TD_EXAMPLE.get("name")

    thing_init_name = ThingInit(name=name_01)
    thing_init_desc = ThingInit(description=TD_EXAMPLE)

    servient = Servient()
    wot = WoT(servient=servient)

    exp_thing_01 = wot.expose(thing_init=thing_init_name).result()

    assert servient.get_exposed_thing(name_01)
    assert exp_thing_01.name == name_01
    assert not len(exp_thing_01.thing.interaction)

    with pytest.raises(ValueError):
        servient.get_exposed_thing(name_02)

    exp_thing_02 = wot.expose(thing_init=thing_init_desc).result()

    assert servient.get_exposed_thing(name_01)
    assert servient.get_exposed_thing(name_02)
    assert exp_thing_02.name == name_02
    assert len(exp_thing_02.thing.interaction)
