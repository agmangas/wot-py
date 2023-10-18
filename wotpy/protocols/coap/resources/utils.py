#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for CoAP resources.
"""

import urllib.parse as parse


def parse_request_opt_query(request):
    """Takes a CoAP Request and returns a dict containing
    the parsed URI query parameters."""

    parsed_dict = parse.parse_qs("&".join(request.opt.uri_query))
    return {key: val[0] for key, val in parsed_dict.items() if len(val)}
