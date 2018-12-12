#!/usr/bin/env python
# -*- coding: utf-8 -*-

from wotpy.support import is_dnssd_supported

if is_dnssd_supported() is False:
    raise NotImplementedError("DNS-SD is not supported in this platform")
