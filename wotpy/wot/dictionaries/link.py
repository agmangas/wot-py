#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
# Copyright (c) 2025 National Technical University of Athens
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

"""
Wrapper classes for link dictionaries defined in the Scripting API.
"""

import urllib

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.wot.dictionaries.security import SecuritySchemeDict
from wotpy.wot.dictionaries.response import ExpectedResponse, AdditionalExpectedResponse


class LinkDict(WotBaseDict):
    """A Web link, as specified by IETF RFC 8288."""

    class Meta:
        fields = {
            "href",
            "type",
            "rel",
            "anchor",
            "sizes",
            "hreflang"
        }

        required = {
            "href"
        }


class FormDict(WotBaseDict):
    """Communication metadata indicating where a service can be accessed
    by a client application. An interaction might have more than one form."""

    class Meta:
        fields = {
            "href",
            "contentType",
            "contentCoding",
            "security",
            "scopes",
            "response",
            "additionalResponses",
            "subprotocol",
            "op"
        }

        required = {
            "href"
        }

        defaults = {
            "contentType": "application/json"
        }

    @property
    def response(self):
        """This optional term can be used if the output communication
        metadata differ from input metadata."""

        return ExpectedResponse(self._init.get("response")) if self._init.get("response") else None

    @property
    def additional_responses(self):
        """This optional term can be used if additional expected
        responses are possible, e.g. for error reporting. Each
        additional response needs to be distinguished from others
        in some way (for example, by specifying a protocol-specific
        error code), and may also have its own data schema."""

        return [AdditionalExpectedResponse(item) for item in self._init.get("additionalResponses", [])]


    def resolve_uri(self, base=None):
        """Resolves and returns the Link URI.
        When the href does not contain a full URL the base URI is joined with said href."""

        href_parsed = urllib.parse.urlparse(self.href)

        if base and not href_parsed.scheme:
            return urllib.parse.urljoin(base, self.href)

        if href_parsed.scheme:
            return self.href

        return None
