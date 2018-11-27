#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
            "scheme",
            "description",
            "proxy"
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
            SecuritySchemeType.BASIC: BasicSecuritySchemeDict,
            SecuritySchemeType.CERT: CertSecuritySchemeDict,
            SecuritySchemeType.DIGEST: DigestSecuritySchemeDict,
            SecuritySchemeType.BEARER: BearerSecuritySchemeDict,
            SecuritySchemeType.PSK: PSKSecuritySchemeDict,
            SecuritySchemeType.PUBLIC: PublicSecuritySchemeDict,
            SecuritySchemeType.OAUTH2: OAuth2SecuritySchemeDict,
            SecuritySchemeType.APIKEY: APIKeySecuritySchemeDict,
            SecuritySchemeType.POP: PoPSecuritySchemeDict
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


class CertSecuritySchemeDict(SecuritySchemeDict):
    """Certificate-base asymmetric key security configuration."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "identity"
        })

        required = SecuritySchemeDict.Meta.required

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.CERT


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


class PublicSecuritySchemeDict(SecuritySchemeDict):
    """Raw public key asymmetric key security configuration."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "identity"
        })

        required = SecuritySchemeDict.Meta.required

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.PUBLIC


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


class PoPSecuritySchemeDict(SecuritySchemeDict):
    """Proof-of-possession token authentication security configuration."""

    class Meta:
        fields = SecuritySchemeDict.Meta.fields.union({
            "alg",
            "authorization",
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

        return SecuritySchemeType.POP
