#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Authenticator classes that perform checks on the incoming requests.
"""

from base64 import b64decode
from abc import ABCMeta, abstractmethod

from wotpy.wot.enums import SecuritySchemeType

class BaseAuthenticator(metaclass=ABCMeta):
    """This is the base authenticator class describing
    the authentication interface."""

    def __init__(self, security_scheme_dict):
        self._security_scheme_dict = security_scheme_dict

    @abstractmethod
    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        raise NotImplementedError()

    @classmethod
    def build(cls, security_scheme_dict):
        """Builds an instance of the appropriate subclass for the given SecurityScheme."""

        klass_map = {
            SecuritySchemeType.NOSEC: NoSecurityAuthenticator,
            SecuritySchemeType.AUTO: AutoSecurityAuthenticator,
            SecuritySchemeType.COMBO: ComboSecurityAuthenticator,
            SecuritySchemeType.BASIC: BasicSecurityAuthenticator,
            SecuritySchemeType.DIGEST: DigestSecurityAuthenticator,
            SecuritySchemeType.APIKEY: APIKeySecurityAuthenticator,
            SecuritySchemeType.BEARER: BearerSecurityAuthenticator,
            SecuritySchemeType.PSK: PSKSecurityAuthenticator,
            SecuritySchemeType.OAUTH2: OAuth2SecurityAuthenticator
        }

        scheme_type = security_scheme_dict.get("scheme")
        klass = klass_map.get(scheme_type)

        if not klass:
            raise ValueError("Unknown scheme: {}".format(scheme_type))

        return klass(security_scheme_dict)


class NoSecurityAuthenticator(BaseAuthenticator):
    """Authenticator that allows all requests."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        return True


class AutoSecurityAuthenticator(BaseAuthenticator):
    """Auto security authenticator."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        raise NotImplementedError()


class ComboSecurityAuthenticator(BaseAuthenticator):
    """Combinator of security schemes authenticator."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        raise NotImplementedError()


class BasicSecurityAuthenticator(BaseAuthenticator):
    """Basic username and password authenticator."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        server_username = server_creds.get("username", None)
        server_password = server_creds.get("password", None)
        valid_server_creds = server_username is not None and server_password is not None

        option = request.opt.get_option(2048)
        if not option:
            return False

        auth_header = option[0].value
        if not auth_header.startswith(b"Basic "):
            return False

        auth_header = auth_header.replace(b"Basic ", b"")
        decoded_string = b64decode(auth_header).decode("ascii")
        username, password = decoded_string.split(":", 1)

        creds_match = (server_username == username and server_password == password)

        return valid_server_creds and creds_match


class DigestSecurityAuthenticator(BaseAuthenticator):
    """Digest authenticator."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        raise NotImplementedError()


class APIKeySecurityAuthenticator(BaseAuthenticator):
    """API Key authenticator."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        raise NotImplementedError()


class BearerSecurityAuthenticator(BaseAuthenticator):
    """Bearer token authenticator."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        raise NotImplementedError()


class PSKSecurityAuthenticator(BaseAuthenticator):
    """Pre shared key authenticator."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        raise NotImplementedError()


class OAuth2SecurityAuthenticator(BaseAuthenticator):
    """OAuth2 authenticator."""

    def authenticate(self, server_creds, request):
        """Checks the credentials of a request."""

        raise NotImplementedError()
