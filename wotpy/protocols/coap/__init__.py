#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
CoAP Protocol Binding implementation.

.. autosummary::
    :toctree: _coap

    wotpy.protocols.coap.resources
    wotpy.protocols.coap.client
    wotpy.protocols.coap.enums
    wotpy.protocols.coap.server
"""

from wotpy.support import is_coap_supported

if is_coap_supported() is False:
    raise NotImplementedError("CoAP binding is not supported in this platform")
