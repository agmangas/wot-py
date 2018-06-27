#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper classes for security dictionaries defined in the Scripting API.
"""

from wotpy.wot.dictionaries.utils import build_init_dict
from wotpy.wot.enums import SecuritySchemeType


class SecuritySchemeDict(object):
    """Contains security related configuration."""

    def __init__(self, *args, **kwargs):
        self._init = build_init_dict(args, kwargs)

        if self.scheme is None:
            raise ValueError("Property 'scheme' is required")

    @classmethod
    def build(cls, *args, **kwargs):
        """Builds an instance of the appropriate subclass for the given SecurityScheme."""

        init_dict = build_init_dict(args, kwargs)

        klass_map = {
            SecuritySchemeType.BASIC: BasicSecuritySchemeDict,
            SecuritySchemeType.DIGEST: DigestSecuritySchemeDict,
            SecuritySchemeType.BEARER: BearerSecuritySchemeDict,
            SecuritySchemeType.POP: PopSecuritySchemeDict,
            SecuritySchemeType.APIKEY: ApikeySecuritySchemeDict,
            SecuritySchemeType.OAUTH2: OAuth2SecuritySchemeDict
        }

        scheme_type = init_dict.get("scheme")
        klass = klass_map.get(scheme_type)

        if not klass:
            raise ValueError("Unknown scheme: {}".format(scheme_type))

        return klass(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return {
            "scheme": self.scheme
        }

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return self._init.get("scheme")


class BasicSecuritySchemeDict(SecuritySchemeDict):
    """Properties that describe a basic security scheme."""

    def __init__(self, *args, **kwargs):
        super(BasicSecuritySchemeDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(BasicSecuritySchemeDict, self).to_dict()

        ret.update({
            "in": self.auth_type,
            "pname": self.pname
        })

        return ret

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.BASIC

    @property
    def auth_type(self):
        """Represents the location of the authentication information."""

        return self._init.get("in")

    @property
    def pname(self):
        """The pname property represents the authentication parameter name."""

        return self._init.get("pname")


class DigestSecuritySchemeDict(SecuritySchemeDict):
    """Properties that describe a digest security scheme."""

    DEFAULT_QOP = "auth"

    def __init__(self, *args, **kwargs):
        super(DigestSecuritySchemeDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(DigestSecuritySchemeDict, self).to_dict()

        ret.update({
            "qop": self.qop
        })

        return ret

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.DIGEST

    @property
    def qop(self):
        """The qop property represents the quality of protection.
        The default value is "auth". The other accepted value is "auth-int"."""

        return self._init.get("qop", self.DEFAULT_QOP)


class BearerSecuritySchemeDict(SecuritySchemeDict):
    """Properties that describe a bearer security scheme."""

    DEFAULT_ALG = "ES256"
    DEFAULT_FORMAT = "jwt"

    def __init__(self, *args, **kwargs):
        super(BearerSecuritySchemeDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(BearerSecuritySchemeDict, self).to_dict()

        ret.update({
            "authorizationURL": self.authorization_url,
            "alg": self.alg,
            "format": self.format
        })

        return ret

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.BEARER

    @property
    def authorization_url(self):
        """Represents the authorization server URL."""

        return self._init.get("authorizationURL", self._init.get("authorization_url"))

    @property
    def alg(self):
        """The alg property represents the encoding, encryption or digest algorithm."""

        return self._init.get("alg", self.DEFAULT_ALG)

    @property
    def format(self):
        """The format property represents the format of the authentication information."""

        return self._init.get("format", self.DEFAULT_FORMAT)


class PopSecuritySchemeDict(SecuritySchemeDict):
    """Properties that describe a proof-of-possession token authentication security scheme."""

    def __init__(self, *args, **kwargs):
        super(PopSecuritySchemeDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return super(PopSecuritySchemeDict, self).to_dict()

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.POP


class ApikeySecuritySchemeDict(SecuritySchemeDict):
    """Properties that describe a API key authentication security scheme."""

    def __init__(self, *args, **kwargs):
        super(ApikeySecuritySchemeDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        return super(ApikeySecuritySchemeDict, self).to_dict()

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.APIKEY


class OAuth2SecuritySchemeDict(SecuritySchemeDict):
    """Properties that describe a OAuth2 security scheme."""

    DEFAULT_FLOW = "implicit"

    def __init__(self, *args, **kwargs):
        super(OAuth2SecuritySchemeDict, self).__init__(*args, **kwargs)

    def to_dict(self):
        """The internal dictionary that contains the entire set of properties."""

        ret = super(OAuth2SecuritySchemeDict, self).to_dict()

        ret.update({
            "tokenURL": self.token_url,
            "authorizationURL": self.authorization_url,
            "refreshURL": self.refresh_url,
            "scopes": self.scopes,
            "flow": self.flow
        })

        return ret

    @property
    def scheme(self):
        """The scheme property represents the identification
        of the security scheme to be used for the Thing."""

        return SecuritySchemeType.OAUTH2

    @property
    def token_url(self):
        """Represents the URL of the token server."""

        return self._init.get("tokenURL", self._init.get("token_url"))

    @property
    def authorization_url(self):
        """Represents the URL of the authorization server."""

        return self._init.get("authorizationURL", self._init.get("authorization_url"))

    @property
    def refresh_url(self):
        """Represents the URL of the refresh server."""

        return self._init.get("refreshURL", self._init.get("refresh_url"))

    @property
    def scopes(self):
        """Represents the authorization scope identifiers as an array of strings."""

        return self._init.get("scopes", [])

    @property
    def flow(self):
        """The flow property represents the authorization flow of type.
        Accepted values are: "implicit" (the default value), "password", "client", or "code"."""

        return self._init.get("flow", self.DEFAULT_FLOW)
