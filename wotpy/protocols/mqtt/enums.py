#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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

"""
Enumeration classes related to the MQTT protocol binding.
"""

from wotpy.utils.enums import EnumListMixin


class MQTTSchemes(EnumListMixin):
    """Enumeration of MQTT schemes."""

    MQTT = "mqtt"
    MQTTS = "mqtts"


class MQTTCommandCodes(EnumListMixin):
    """Enumeration of MQTT packet types."""

    PUBLISH = 3
    SUBSCRIBE = 8
    UNSUBSCRIBE = 10


class MQTTQoSLevels(EnumListMixin):
    """Enumeration of MQTT Quality of Service levels."""

    FIRE_FORGET = 0
    AT_LEAST_ONCE = 1
    EXACTLY_ONCE = 2


class MQTTVocabularyKeys(EnumListMixin):
    """Enumeration of terms that form the MQTT vocabulary that may appear in TD Form elements."""

    COMMAND_CODE = "mqtt:commandCode"
    OPTIONS = "mqtt:options"
    OPTION_NAME = "mqtt:optionName"
    OPTION_VALUE = "mqtt:optionValue"
    OPTION_NAME_QOS = "mqtt:qos"
    OPTION_NAME_RETAIN = "mqtt:retain"
    OPTION_NAME_DUP = "mqtt:dup"


class MQTTCodesACK(EnumListMixin):
    """Enumeration of MQTT ACK codes."""

    CON_OK = 0
    SUB_ERROR = 128
