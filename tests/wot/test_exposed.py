#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from faker import Faker

from tests.utils import FutureTimeout
from wotpy.wot.dictionaries import ThingPropertyInit
from wotpy.wot.exposed import ExposedThing


@pytest.fixture
def exposed_empty():
    """Fixture that creates an empty ExposedThing."""

    fake = Faker()

    # ToDo: Set the Servient
    return ExposedThing.from_name(servient=None, name=fake.user_name())


@pytest.fixture
def prop_init():
    """Fixture that creates a ThingPropertyInit."""

    fake = Faker()

    return ThingPropertyInit(
        name=fake.user_name(),
        value=fake.pystr(),
        description={"type": "string"})


# noinspection PyShadowingNames
def test_get_property(exposed_empty, prop_init):
    """Properties may be retrieved on ExposedThings."""

    exposed_empty.add_property(property_init=prop_init)
    future_get = exposed_empty.get_property(prop_init.name)

    assert future_get.result(timeout=FutureTimeout.MINIMAL) == prop_init.value


# noinspection PyShadowingNames
def test_set_property(exposed_empty, prop_init):
    """Properties may be updated on ExposedThings."""

    fake = Faker()

    prop_init.writable = True
    exposed_empty.add_property(property_init=prop_init)
    updated_val = fake.pystr()
    future_set = exposed_empty.set_property(prop_init.name, updated_val)
    future_set.result(timeout=FutureTimeout.MINIMAL)
    future_get = exposed_empty.get_property(prop_init.name)

    assert future_get.result(timeout=FutureTimeout.MINIMAL) == updated_val


# noinspection PyShadowingNames
def test_on_retrieve_property(exposed_empty, prop_init):
    """Custom handlers to retrieve properties can be defined on ExposedThings."""

    fake = Faker()
    dummy_value = fake.pystr()

    def _handler_dummy(request):
        request.respond(dummy_value)

    def _handler_error(request):
        request.respond_with_error(ValueError())

    exposed_empty.add_property(property_init=prop_init)
    exposed_empty.on_retrieve_property(_handler_dummy)
    future_get_01 = exposed_empty.get_property(prop_init.name)

    assert future_get_01.result(timeout=FutureTimeout.MINIMAL) == dummy_value

    future_set = exposed_empty.set_property(prop_init.name, fake.pystr())
    future_set.result(timeout=FutureTimeout.MINIMAL)
    future_get_02 = exposed_empty.get_property(prop_init.name)

    assert future_get_02.result(timeout=FutureTimeout.MINIMAL) == dummy_value

    exposed_empty.on_retrieve_property(_handler_error)
    future_get_03 = exposed_empty.get_property(prop_init.name)

    with pytest.raises(ValueError):
        future_get_03.result(timeout=FutureTimeout.MINIMAL)
