#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
MQTT Protocol Binding implementation.

.. autosummary::
    :toctree: _mqtt

    wotpy.protocols.mqtt.handlers
    wotpy.protocols.mqtt.client
    wotpy.protocols.mqtt.enums
    wotpy.protocols.mqtt.runner
    wotpy.protocols.mqtt.server
"""

from wotpy.support import is_mqtt_supported

if is_mqtt_supported() is False:
    raise NotImplementedError("MQTT binding is not supported in this platform")
