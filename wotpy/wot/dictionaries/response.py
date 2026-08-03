#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for expected responses.
"""

from wotpy.wot.dictionaries.base import WotBaseDict


class ExpectedResponse(WotBaseDict):
    """Communication metadata describing the expected response
    message for the primary response."""

    class Meta:
        fields = {
            "contentType"
        }

        required = {
            "contentType"
        }


class AdditionalExpectedResponse(WotBaseDict):
    """Communication metadata describing the expected response
    message for additional responses."""

    class Meta:
        fields = {
            "success",
            "contentType",
            "schema"
        }

        required = {
            "contentType"
        }

        defaults = {
            "success": False
        }
