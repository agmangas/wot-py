#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2017 CTIC Centro Tecnologico
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
Class that serves as the WoT entrypoint.
"""

import json
import logging

import reactivex
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from wotpy.protocols.http.credential import OIDC4VPCredential
from wotpy.wot.consumed.thing import ConsumedThing
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.enums import DiscoveryMethod
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing

DEFAULT_FETCH_TIMEOUT_SECS = 20.0


class WoT:
    """The WoT object is the API entry point and it is exposed by an
    implementation of the WoT Runtime. The WoT object does not expose
    properties, only methods for discovering, consuming and exposing a Thing."""

    def __init__(self, servient):
        self._servient = servient
        self._logr = logging.getLogger(__name__)
        # Create overridable ExposedThing class
        self._exposed_thing_cls = ExposedThing

    def set_exposed_thing_class(self, cls):
        self._exposed_thing_cls = cls

    @property
    def servient(self):
        """Servient instance of this WoT entrypoint."""

        return self._servient

    @classmethod
    def _is_fragment_match(cls, item, thing_filter):
        """Returns True if the given item (an ExposedThing, Thing or TD)
        matches the fragment in the given Thing filter."""

        td = None

        if isinstance(item, ExposedThing):
            td = ThingDescription.from_thing(item.thing)
        elif isinstance(item, Thing):
            td = ThingDescription.from_thing(item)
        elif isinstance(item, ThingDescription):
            td = item

        assert td

        fragment_dict = thing_filter.fragment if thing_filter.fragment else {}

        return all(
            item in td.to_dict().items()
            for item in fragment_dict.items())

    def _build_local_discover_observable(self, thing_filter):
        """Builds an Observable to discover Things using the local method."""

        found_tds = [
            ThingDescription.from_thing(exposed_thing.thing).to_str()
            for exposed_thing in self._servient.exposed_things
            if self._is_fragment_match(exposed_thing, thing_filter)
        ]

        return reactivex.of(*found_tds)

    async def _get_verifiable_creds_token(self, url, credentials_dict):
        """Queries the OIDC4VP holder for a token."""

        if credentials_dict is not None:
            if url in self.servient._access_tokens:
                token = self.servient._access_tokens[url]
                self._logr.log(logging.DEBUG, f"Token for '{url}' already stored: {token}")
            else:
                holder_url = credentials_dict.get("holder_url", None)
                requester = credentials_dict.get("requester", None)
                if holder_url is None:
                    raise ValueError("Missing Verifiable credentials holder url")
                if requester is None:
                    raise ValueError("Missing Verifiable credentials requester URL/IP")

                token = await OIDC4VPCredential.holder_token_request(
                    holder_url, url, "GET", requester
                )
                self.servient._access_tokens[url] = token
                self._logr.log(logging.DEBUG, f"Stored token for '{url}': {token}")
            headers = {"X-Auth-token": token}
            return headers

        return None

    def discover(self, thing_filter):
        """Starts the discovery process that will provide ThingDescriptions
        that match the optional argument filter of type ThingFilter."""

        supported_methods = [
            DiscoveryMethod.ANY,
            DiscoveryMethod.LOCAL
        ]

        if thing_filter.method not in supported_methods:
            err = NotImplementedError("Unsupported discovery method")
            return reactivex.throw(err)

        if thing_filter.query:
            err = NotImplementedError(
                "Queries are not supported yet (please use filter.fragment)")
            return reactivex.throw(err)

        observables = []

        if thing_filter.method in [DiscoveryMethod.ANY, DiscoveryMethod.LOCAL]:
            observables.append(
                self._build_local_discover_observable(thing_filter))

        return reactivex.merge(*observables)

    @classmethod
    async def fetch(cls, url, headers=None, timeout_secs=None):
        """Accepts an url argument and returns a Future
        that resolves with a Thing Description string."""

        timeout_secs = timeout_secs or DEFAULT_FETCH_TIMEOUT_SECS

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, headers=headers, request_timeout=timeout_secs)

        http_response = await http_client.fetch(http_request)

        td_doc = json.loads(http_response.body)
        td = ThingDescription(td_doc)

        return td.to_str()

    def consume(self, td_str):
        """Accepts a thing description string argument and returns a
        ConsumedThing object instantiated based on that description."""

        td = ThingDescription(td_str)

        return ConsumedThing(servient=self._servient, td=td)

    @classmethod
    def thing_from_model(cls, model):
        """Takes a ThingModel and builds a Thing.
        Raises if the model has an unexpected type."""

        expected_types = (str, ThingFragment, ConsumedThing)

        if not isinstance(model, expected_types):
            raise ValueError("Expected one of: {}".format(expected_types))

        if isinstance(model, str):
            thing = ThingDescription(doc=model).build_thing()
        elif isinstance(model, ThingFragment):
            thing = Thing(thing_fragment=model)
        else:
            thing = model.td.build_thing()

        return thing

    def produce(self, model):
        """Accepts a model argument of type ThingModel and returns an ExposedThing
        object, locally created based on the provided initialization parameters."""

        thing = self.thing_from_model(model)
        exposed_thing = self._exposed_thing_cls(servient=self._servient, thing=thing)
        self._servient.add_exposed_thing(exposed_thing)

        return exposed_thing

    async def produce_from_url(self, url, timeout_secs=None):
        """Return a Future that resolves to an ExposedThing created
        from the thing description retrieved from the given URL."""

        td_str = await self.fetch(url, timeout_secs=timeout_secs)
        exposed_thing = self.produce(td_str)

        return exposed_thing

    async def consume_from_url(self, url, credentials_dict=None, timeout_secs=None):
        """Return a Future that resolves to a ConsumedThing created
        from the thing description retrieved from the given URL."""

        headers = await self._get_verifiable_creds_token(url, credentials_dict)

        td_str = await self.fetch(url, headers=headers, timeout_secs=timeout_secs)

        # Invalid credential
        if td_str is None:
            self.servient._access_tokens.pop(url, None)
            headers = await self._get_verifiable_creds_token(url, credentials_dict)
            td_str = await self.fetch(url, headers=headers, timeout_secs=timeout_secs)

            if td_str is None:
                raise Exception("Error when retrieving access token")

        consumed_thing = self.consume(td_str)

        return consumed_thing

    async def register(self, directory, thing):
        """Generate the Thing Description as td, given the Properties,
        Actions and Events defined for this ExposedThing object.
        Then make a request to register td to the given WoT Thing Directory."""

        raise NotImplementedError()

    async def unregister(self, directory, thing):
        """Makes a request to unregister the thing from the given WoT Thing Directory."""

        raise NotImplementedError()
