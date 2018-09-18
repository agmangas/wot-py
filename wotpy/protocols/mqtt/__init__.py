#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.protocols.support import is_mqtt_supported

if is_mqtt_supported() is False:
    raise NotImplementedError("MQTT binding is not supported in this platform")
