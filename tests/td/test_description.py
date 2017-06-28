#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy

# noinspection PyPackageRequirements
import pytest
from jsonschema import ValidationError

from tests.utils import random_dict_mess
from wotpy.td.description import ThingDescription

TEST_TD = {
    "@context": [
        "http://w3c.github.io/wot/w3c-wot-td-context.jsonld",
        {"actuator": "http://example.org/actuator#"}
    ],
    "@type": ["Thing"],
    "name": "MyLEDThing",
    "base": "coap://myled.example.com:5683/",
    "security": {
        "cat": "token:jwt",
        "alg": "HS256",
        "as": "https://authority-issuing.example.org"
    },
    "interaction": [{
        "@type": ["Property", "actuator:onOffStatus"],
        "name": "status",
        "outputData": {"type": "boolean"},
        "writable": True,
        "link": [{
            "href": "pwr",
            "mediaType": "application/exi"
        }, {
            "href": "http://mytemp.example.com:8080/status",
            "mediaType": "application/json"
        }]
    }, {
        "@type": ["Action", "actuator:fadeIn"],
        "name": "fadeIn",
        "inputData": {"type": "integer"},
        "link": [{
            "href": "in",
            "mediaType": "application/exi"
        }, {
            "href": "http://mytemp.example.com:8080/in",
            "mediaType": "application/json"
        }]
    }, {
        "@type": ["Action", "actuator:fadeOut"],
        "name": "fadeOut",
        "inputData": {"type": "integer"},
        "link": [{
            "href": "out",
            "mediaType": "application/exi"
        }, {
            "href": "http://mytemp.example.com:8080/out",
            "mediaType": "application/json"
        }]
    }, {
        "@type": ["Event", "actuator:alert"],
        "name": "criticalCondition",
        "outputData": {"type": "string"},
        "link": [{
            "href": "ev",
            "mediaType": "application/exi"
        }]
    }]
}


def test_validate_td_ok():
    """Example 'MyLEDThing' TD from W3C GitHub page validates correctly."""

    thing_description = ThingDescription(TEST_TD)
    thing_description.validate()


def test_validate_td_err():
    """An erroneous TD raises error on validation."""

    for _ in range(10):
        td_dict = copy.deepcopy(TEST_TD)
        random_dict_mess(td_dict, num_updates=20, existing_keys_only=True)

        with pytest.raises(ValidationError):
            thing_description_err = ThingDescription(td_dict)
            thing_description_err.validate()
