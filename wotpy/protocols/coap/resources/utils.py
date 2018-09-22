#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for CoAP resources.
"""

import six

from six.moves.urllib import parse


def parse_request_opt_query(request):
    """Takes a CoAP Request and returns a dict containing
    the parsed URI query parameters."""

    parsed_dict = parse.parse_qs("&".join(request.opt.uri_query))
    return {key: val[0] for key, val in six.iteritems(parsed_dict) if len(val)}
