#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging

from wotpy.wot.discovery.support import is_dnssd_supported

collect_ignore = []

if not is_dnssd_supported():
    logging.warning("Skipping DNS-SD tests due to unsupported platform")
    collect_ignore.extend(["test_service.py"])
