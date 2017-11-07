#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
from faker import Faker

from wotpy.wot.servient import Servient
from wotpy.wot.exposed import ExposedThing
from wotpy.wot.dictionaries import \
    ThingPropertyInit, \
    ThingEventInit, \
    ThingActionInit


@pytest.fixture
def thing_property_init():
    """Builds and returns a random ThingPropertyInit."""

    fake = Faker()

    return ThingPropertyInit(
        name=fake.user_name(),
        value=fake.pystr(),
        description={"type": "string"})


@pytest.fixture
def thing_event_init():
    """Builds and returns a random ThingEventInit."""

    fake = Faker()

    return ThingEventInit(
        name=fake.user_name(),
        data_description={"type": "string"})


@pytest.fixture
def thing_action_init():
    """Builds and returns a random ThingActionInit."""

    fake = Faker()

    def _upper(val):
        return val.upper()

    return ThingActionInit(
        name=fake.user_name(),
        action=_upper,
        input_data_description={"type": "string"},
        output_data_description={"type": "string"})


@pytest.fixture
def exposed_thing():
    """Builds and returns a random ExposedThing."""

    fake = Faker()

    servient = Servient()

    return ExposedThing.from_name(
        servient=servient,
        name=fake.user_name())
