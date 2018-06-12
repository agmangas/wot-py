#!/usr/bin/env python
# -*- coding: utf-8 -*-

TD_EXAMPLE = {
    "id": "urn:dev:wot:com:example:servient:lamp",
    "name": "MyLampThing",
    "description": "MyLampThing uses JSON-LD 1.1 serialization",
    "properties": {
        "status": {
            "description": "Shows the current status of the lamp",
            "type": "string",
            "forms": [{
                "href": "coaps://mylamp.example.com:5683/status"
            }]
        }
    },
    "actions": {
        "toggle": {
            "description": "Turn on or off the lamp.",
            "forms": [{
                "href": "coaps://mylamp.example.com:5683/toggle"
            }]
        }
    },
    "events": {
        "overheating": {
            "description": "Lamp reaches a critical temperature (overheating).",
            "type": "string",
            "forms": [{
                "href": "coaps://mylamp.example.com:5683/oh"
            }]
        }
    }
}
