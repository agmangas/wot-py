#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from wotpy.protocols.support import is_coap_supported

collect_ignore = []

if not is_coap_supported():
    logging.warning("Skipping CoAP tests due to unsupported platform")
    collect_ignore += ["test_server.py"]
