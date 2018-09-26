#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enumeration classes related to the MQTT protocol binding.
"""

from wotpy.utils.enums import EnumListMixin


class MQTTSchemes(EnumListMixin):
    """Enumeration of MQTT schemes."""

    MQTT = "mqtt"


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
