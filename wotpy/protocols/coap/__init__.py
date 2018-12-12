#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.support import is_coap_supported

if is_coap_supported() is False:
    raise NotImplementedError("CoAP binding is not supported in this platform")
