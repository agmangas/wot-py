#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import copy

# noinspection PyPackageRequirements
import pytest
from jsonschema import ValidationError

from tests.utils import random_dict_mess
from wotpy.td.description import ThingDescription
from wotpy.td.interaction import Interaction, InteractionTypes

TEST_TD = {
    '@context': [
        'http://w3c.github.io/wot/w3c-wot-td-context.jsonld',
        {'actuator': 'http://example.org/actuator#'}
    ],
    '@type': ['Thing'],
    'name': 'MyLEDThing',
    'base': 'coap://myled.example.com:5683/',
    'security': {
        'cat': 'token:jwt',
        'alg': 'HS256',
        'as': 'https://authority-issuing.example.org'
    },
    'interaction': [{
        '@type': ['Property', 'actuator:onOffStatus'],
        'name': 'status',
        'outputData': {'type': 'boolean'},
        'writable': True,
        'link': [{
            'href': 'pwr',
            'mediaType': 'application/exi'
        }, {
            'href': 'http://mytemp.example.com:8080/status',
            'mediaType': 'application/json'
        }]
    }, {
        '@type': ['Action', 'actuator:fadeIn'],
        'name': 'fadeIn',
        'inputData': {'type': 'integer'},
        'link': [{
            'href': 'in',
            'mediaType': 'application/exi'
        }, {
            'href': 'http://mytemp.example.com:8080/in',
            'mediaType': 'application/json'
        }]
    }, {
        '@type': ['Action', 'actuator:fadeOut'],
        'name': 'fadeOut',
        'inputData': {'type': 'integer'},
        'link': [{
            'href': 'out',
            'mediaType': 'application/exi'
        }, {
            'href': 'http://mytemp.example.com:8080/out',
            'mediaType': 'application/json'
        }]
    }, {
        '@type': ['Event', 'actuator:alert'],
        'name': 'criticalCondition',
        'outputData': {'type': 'string'},
        'link': [{
            'href': 'ev',
            'mediaType': 'application/exi'
        }]
    }]
}

TEST_INTERACTION = {
    '@type': ['Property', 'actuator:onOffStatus'],
    'name': 'status',
    'outputData': {'type': 'boolean'},
    'writable': True,
    'link': [{
        'href': 'pwr',
        'mediaType': 'application/exi'
    }, {
        'href': 'http://mytemp.example.com:8080/status',
        'mediaType': 'application/json'
    }]
}


def test_thing_description_validate():
    """Example Thing Description from W3C GitHub page validates correctly."""

    thing_description = ThingDescription(TEST_TD)
    thing_description.validate()


def test_thing_description_properties():
    """Properties can be retrieved from Thing Description objects."""

    thing_description = ThingDescription(TEST_TD)

    assert thing_description.name == TEST_TD.get('name')
    assert thing_description.base == TEST_TD.get('base')
    assert len(thing_description.interaction) == len(TEST_TD.get('interaction', []))


def test_thing_description_validate_err():
    """An erroneous Thing Description raises error on validation."""

    def random_builder():
        return [
            random.random(),
            int(random.random()),
            [random.random() for _ in range(random.randint(1, 10))]
        ]

    td_dict = copy.deepcopy(TEST_TD)
    random_dict_mess(td_dict, random_builder=random_builder)

    with pytest.raises(ValidationError):
        thing_description_err = ThingDescription(td_dict)
        thing_description_err.validate()


def test_interaction_properties():
    """Properties can be retrieved from Interaction objects."""

    interaction = Interaction(TEST_INTERACTION)

    assert interaction.interaction_type == InteractionTypes.PROPERTY
    assert interaction.name == TEST_INTERACTION.get('name')
    assert len(interaction.link) == len(TEST_INTERACTION.get('link', []))
