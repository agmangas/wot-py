#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Credential classes that add the proper authorization creds to the outgoing requests.
"""

import json
from base64 import b64encode
from abc import ABCMeta, abstractmethod
from urllib.parse import urlparse

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session
from tornado.httpclient import AsyncHTTPClient, HTTPRequest
from tornado.web import HTTPError

from wotpy.wot.enums import SecuritySchemeType


class BaseCredential(metaclass=ABCMeta):
    """This is the base credential class describing
    the credential interface."""

    def __init__(self, security_scheme_dict, security_credentials):
        self._security_scheme_dict = security_scheme_dict
        self._security_credentials = security_credentials

    @abstractmethod
    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        raise NotImplementedError()

    @classmethod
    def build(cls, security_scheme_dict, security_credentials):
        """Builds an instance of the appropriate subclass for the given SecurityScheme."""

        klass_map = {
            SecuritySchemeType.NOSEC: NoSecurityCredential,
            SecuritySchemeType.AUTO: AutoSecurityCredential,
            SecuritySchemeType.COMBO: ComboSecurityCredential,
            SecuritySchemeType.BASIC: BasicSecurityCredential,
            SecuritySchemeType.DIGEST: DigestSecurityCredential,
            SecuritySchemeType.APIKEY: APIKeySecurityCredential,
            SecuritySchemeType.BEARER: BearerSecurityCredential,
            SecuritySchemeType.PSK: PSKSecurityCredential,
            SecuritySchemeType.OAUTH2: OAuth2SecurityCredential,
            SecuritySchemeType.OIDC4VP: OIDC4VPCredential
        }

        scheme_type = security_scheme_dict.get("scheme")
        klass = klass_map.get(scheme_type)

        if not klass:
            raise ValueError("Unknown scheme: {}".format(scheme_type))

        return klass(security_scheme_dict, security_credentials)


class NoSecurityCredential(BaseCredential):
    """Credential that allows all requests."""

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        return request


class AutoSecurityCredential(BaseCredential):
    """Auto security credential."""

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        raise NotImplementedError()


class ComboSecurityCredential(BaseCredential):
    """Combinator of security schemes credential."""

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        raise NotImplementedError()


class BasicSecurityCredential(BaseCredential):
    """Basic username and password credential."""

    def __init__(self, security_scheme_dict, security_credentials):
        super().__init__(security_scheme_dict, security_credentials)
        self._username = security_credentials.get("username", None)
        self._password = security_credentials.get("password", None)

        if self._username is None:
            raise ValueError("Missing HTTP username")
        if self._password is None:
            raise ValueError("Missing HTTP password")

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        encoded_creds = b64encode(f"{self._username}:{self._password}".encode("ascii"))
        encoded_creds_str = encoded_creds.decode("ascii")
        auth_header = f"Basic {encoded_creds_str}"
        request.headers["Authorization"] = auth_header

        return request


class DigestSecurityCredential(BaseCredential):
    """Digest credential."""

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        raise NotImplementedError()


class APIKeySecurityCredential(BaseCredential):
    """API Key credential."""

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        raise NotImplementedError()


class BearerSecurityCredential(BaseCredential):
    """Bearer token credential."""

    def __init__(self, security_scheme_dict, security_credentials):
        super().__init__(security_scheme_dict, security_credentials)
        self._token = security_credentials.get("token", None)

        if self._token is None:
            raise ValueError("Missing HTTP token")

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        auth_header = f"Bearer {self._token}"
        request.headers["Authorization"] = auth_header

        return request


class PSKSecurityCredential(BaseCredential):
    """Pre shared key credential."""

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        raise NotImplementedError()


class OAuth2SecurityCredential(BaseCredential):
    """OAuth2 credential."""

    def __init__(self, security_scheme_dict, security_credentials):
        super().__init__(security_scheme_dict, security_credentials)

        self._flow = security_scheme_dict.get("flow", None)
        if self._flow == "client":
            self._client_id = security_credentials.get("clientId", None)
            self._client_secret = security_credentials.get("clientSecret", None)

            self._token_uri = security_scheme_dict.get("token", None)
            self._scopes = security_scheme_dict.get("scopes", None)

            client = BackendApplicationClient(client_id=self._client_id)
            oauth = OAuth2Session(client=client, scope=self._scopes)

            self._token = oauth.fetch_token(
                token_url=self._token_uri, client_id=self._client_id, client_secret=self._client_secret)

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        auth_header = f"Bearer {self._token['access_token']}"
        request.headers["Authorization"] = auth_header

        return request


class OIDC4VPCredential(BaseCredential):
    """OpenID Connect for Verifiable Presentations credential."""

    def __init__(self, security_scheme_dict, security_credentials):
        super().__init__(security_scheme_dict, security_credentials)
        self._access_tokens = {}
        self._holder_url = security_credentials.get("holder_url", None)
        self._requester = security_credentials.get("requester", None)

        if self._holder_url is None:
            raise ValueError("Missing Verifiable credentials holder url")
        if self._requester is None:
            raise ValueError("Missing Verifiable credentials requester URL/IP")

    @staticmethod
    async def holder_token_request(holder_url, target_url, method, requester):
        """Function that makes a call to the holder to create a new token
        that can then be sent along with an HTTP request."""

        url = urlparse(target_url)
        device = f"{url.scheme}://{url.netloc}"
        # Resource starts after the device prefix
        resource = target_url[len(device):]

        body = json.dumps({
            "device": device,
            "method": method,
            "resource": resource,
            "requester": requester
        })

        headers = {
            "Content-Type": "application/json"
        }

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(
            f"{holder_url}/auth", method="POST", headers=headers, body=body
        )

        try:
            response = await http_client.fetch(http_request)

            token_response = response.body.decode('utf8').replace('\n', '')
            return token_response
        except HTTPError as error:
            raise error
        except Exception as exc:
            raise HTTPError(status_code=500, log_message="Internal server error") from exc

    async def sign(self, request):
        """Adds the appropriate authorization header to the request."""

        if request.url in self._access_tokens:
            token = self._access_tokens[request.url]
        else:
            token = await self.holder_token_request(
                self._holder_url, request.url, request.method, self._requester
            )
            self._access_tokens[request.url] = token

        request.headers["X-Auth-Token"] = token

        return request
