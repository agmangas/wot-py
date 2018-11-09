#!/usr/bin/env python
# -*- coding: utf-8 -*-

TD_EXAMPLE = {
    "id": "urn:dev:wot:com:example:servient:lamp",
    "name": "MyLampThing",
    "description": "MyLampThing uses JSON-LD 1.1 serialization",
    "security": [{"scheme": "nosec"}],
    "properties": {
        "status": {
            "description": "Shows the current status of the lamp",
            "type": "string",
            "forms": [{
                "href": "coaps://mylamp.example.com/status"
            }]
        }
    },
    "actions": {
        "toggle": {
            "description": "Turn on or off the lamp",
            "forms": [{
                "href": "coaps://mylamp.example.com/toggle"
            }]
        }
    },
    "events": {
        "overheating": {
            "description": "Lamp reaches a critical temperature (overheating)",
            "data": {"type": "string"},
            "forms": [{
                "href": "coaps://mylamp.example.com/oh"
            }]
        }
    }
}
