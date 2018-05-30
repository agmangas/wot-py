#!/usr/bin/env python
# -*- coding: utf-8 -*-

import uuid

# noinspection PyPackageRequirements
import pytest
# noinspection PyPackageRequirements
from faker import Faker

from wotpy.td.thing import Thing
from wotpy.wot.dictionaries import ThingPropertyInit, ThingEventInit, ThingActionInit
from wotpy.wot.exposed import ExposedThing
from wotpy.wot.servient import Servient


@pytest.fixture
def thing_property_init():
    """Builds and returns a random ThingPropertyInit."""

    fake = Faker()

    return ThingPropertyInit(
        name=fake.user_name(),
        value=fake.pystr(),
        data_type={"type": "string"})


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

    return ThingActionInit(
        name=fake.user_name(),
        input_data_description={"type": "string"},
        output_data_description={"type": "string"})


@pytest.fixture
def exposed_thing():
    """Builds and returns a random ExposedThing."""

    return ExposedThing(
        servient=Servient(),
        thing=Thing(id=uuid.uuid4().urn))
