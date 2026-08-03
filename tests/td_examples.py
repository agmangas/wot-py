#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

from wotpy.wot.constants import WOT_TD_CONTEXT_URL_V1_1

TD_EXAMPLE = {
    "@context": [
        WOT_TD_CONTEXT_URL_V1_1
    ],
    "id": "urn:dev:wot:com:example:servient:lamp",
    "title": "MyLampThing",
    "description": "MyLampThing uses JSON-LD 1.1 serialization",
    "security": ["nosec_sc"],
    "securityDefinitions": {
        "nosec_sc": {"scheme": "nosec"}
    },
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
