#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for link dictionaries defined in the Scripting API.
"""

from wotpy.wot.dictionaries.utils import build_init_dict


class LinkDict(object):
    """A link to an external resource that may be related to the Thing in any way."""

    def __init__(self, *args, **kwargs):
        self._init = build_init_dict(args, kwargs)

        if self.href is None:
            raise ValueError("Property 'href' is required")

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return self._init

    @property
    def href(self):
        """The href property is a hypertext reference that defines the Link."""

        return self._init.get("href")

    @property
    def media_type(self):
        """The mediaType property represents the IANA media type associated with the Link."""

        return self._init.get("mediaType", self._init.get("media_type"))

    @property
    def rel(self):
        """The rel property represents a semantic label that
        specifies how to interact with the linked resource."""

        return self._init.get("rel")


class WebLinkDict(LinkDict):
    """A Link from a Thing to a resource that exists on the Web."""

    def __init__(self, *args, **kwargs):
        super(WebLinkDict, self).__init__(*args, **kwargs)

    @property
    def anchor(self):
        """The anchor property represents a URI that
        overrides the default context of a Link."""

        return self._init.get("anchor")


class FormDict(LinkDict):
    """A dictionary that describes a connection endpoint for an interaction."""

    def __init__(self, *args, **kwargs):
        super(FormDict, self).__init__(*args, **kwargs)

    @property
    def security(self):
        """The security property represents the security
        requirements for the linked resource."""

        return self._init.get("security")
