#!/usr/bin/env python
# -*- coding: utf-8 -*-

TD_EXAMPLE = {
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
        "observable": True,
        "form": [{
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
        "form": [{
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
        "form": [{
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
        "form": [{
            "href": "ev",
            "mediaType": "application/exi"
        }]
    }]
}
