#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for link dictionaries defined in the Scripting API.
"""

from six.moves import urllib

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.wot.dictionaries.security import SecuritySchemeDict


class LinkDict(WotBaseDict):
    """A Web link, as specified by IETF RFC 8288."""

    class Meta:
        fields = {
            "href",
            "type",
            "rel",
            "anchor"
        }

        required = {
            "href"
        }


class FormDict(LinkDict):
    """Communication metadata indicating where a service can be accessed
    by a client application. An interaction might have more than one form."""

    class Meta:
        fields = LinkDict.Meta.fields.union({
            "href",
            "contentType",
            "op",
            "subprotocol",
            "security",
            "scopes"
        })

        required = LinkDict.Meta.required.union({
            "href"
        })

        defaults = {
            "contentType": "application/json"
        }

    @property
    def security(self):
        """Set of security configurations, provided as an array,
        that must all be satisfied for access to resources at or
        below the current level, if not overridden at a lower level"""

        if "security" not in self._init:
            return None

        return [SecuritySchemeDict.build(item) for item in self._init.get("security")]

    def resolve_uri(self, base=None):
        """Resolves and returns the Link URI.
        When the href does not contain a full URL the base URI is joined with said href."""

        href_parsed = urllib.parse.urlparse(self.href)

        if base and not href_parsed.scheme:
            return urllib.parse.urljoin(base, self.href)

        if href_parsed.scheme:
            return self.href

        return None
