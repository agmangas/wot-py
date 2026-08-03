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
Wrapper classes for security dictionaries defined in the Scripting API.
"""

from wotpy.wot.dictionaries.base import WotBaseDict
from wotpy.utils.utils import merge_args_kwargs_dict
from wotpy.wot.enums import SecuritySchemeType


class SecuritySchemeDict(WotBaseDict):
    """Contains security related configuration."""

    class Meta:
        fields = {
            "@type",
            "description",
            "descriptions",
            "proxy",
            "scheme"
        }

        required = {
            "scheme"
        }

    @classmethod
    def build(cls, *args, **kwargs):
        """Builds an instance of the appropriate subclass for the given SecurityScheme."""

        init_dict = merge_args_kwargs_dict(args, kwargs)

        klass_map = {
            SecuritySchemeType.NOSEC: NoSecuritySchemeDict,
            SecuritySchemeType.AUTO: AutoSecuritySchemeDict,
            SecuritySchemeType.COMBO: ComboSecuritySchemeDict,
            SecuritySchemeType.BASIC: BasicSecuritySchemeDict,
            SecuritySchemeType.DIGEST: DigestSecuritySchemeDict,
            SecuritySchemeType.APIKEY: APIKeySecuritySchemeDict,
            SecuritySchemeType.BEARER: BearerSecuritySchemeDict,
            SecuritySchemeType.PSK: PSKSecuritySchemeDict,
            SecuritySchemeType.OAUTH2: OAuth2SecuritySchemeDict
        }

        scheme_type = init_dict.get("scheme")
        klass = klass_map.get(scheme_type)

        if not klass:
            raise ValueError("Unknown scheme: {}".format(scheme_type))

        return klass(*args, **kwargs)


class NoSecuritySchemeDict(SecuritySchemeDict):
    """A security configuration indicating there is no authentication
    or other mechanism required to access the resource."""

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.NOSEC


class AutoSecuritySchemeDict(SecuritySchemeDict):
    """An automatic authentication security configuration indicating
    that the security parameters are going to be negotiated by
    the underlying protocols at runtime."""

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.AUTO


class ComboSecuritySchemeDict(SecuritySchemeDict):
    """A combination of other security schemes. Elements of this scheme define
    various ways in which other named schemes defined in securityDefinitions,
    including other ComboSecurityScheme definitions, are to be combined to
    create a new scheme definition."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "oneOf",
            "allOf"
        })

        required = SecuritySchemeDict.Meta.required

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.COMBO


class BasicSecuritySchemeDict(SecuritySchemeDict):
    """Basic authentication security configuration using an unencrypted username and password."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "in",
            "name"
        })

        required = SecuritySchemeDict.Meta.required

        defaults = {
            "in": "header"
        }

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.BASIC


class DigestSecuritySchemeDict(SecuritySchemeDict):
    """Digest authentication security configuration. This scheme is similar to
    basic authentication but with added features to avoid man-in-the-middle attacks."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "qop",
            "in",
            "name"
        })

        required = SecuritySchemeDict.Meta.required

        defaults = {
            "qop": "auth",
            "in": "header"
        }

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.DIGEST


class APIKeySecuritySchemeDict(SecuritySchemeDict):
    """API key authentication security configuration.
    This is for the case where the access token is opaque and is not using a standard token format."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "in",
            "name"
        })

        required = SecuritySchemeDict.Meta.required

        defaults = {
            "in": "query"
        }

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.APIKEY


class BearerSecuritySchemeDict(SecuritySchemeDict):
    """Bearer token authentication security configuration. This scheme is intended
    for situations where bearer tokens are used independently of OAuth2.
    If the oauth2 scheme is specified it is not generally necessary to
    specify this scheme as well as it is implied."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "authorization",
            "alg",
            "format",
            "in",
            "name"
        })

        required = SecuritySchemeDict.Meta.required

        defaults = {
            "alg": "ES256",
            "format": "jwt",
            "in": "header"
        }

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.BEARER


class PSKSecuritySchemeDict(SecuritySchemeDict):
    """Pre-shared key authentication security configuration."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "identity"
        })

        required = SecuritySchemeDict.Meta.required

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.PSK


class OAuth2SecuritySchemeDict(SecuritySchemeDict):
    """OAuth2 authentication security configuration.
    For the implicit flow the authorization and scopes are required.
    For the password and client flows both token and scopes are required.
    For the code flow authorization, token, and scopes are required."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "authorization",
            "token",
            "refresh",
            "scopes",
            "flow"
        })

        required = SecuritySchemeDict.Meta.required

        defaults = {
            "flow": "implicit"
        }

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.OAUTH2
