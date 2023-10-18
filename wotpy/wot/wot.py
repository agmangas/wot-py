#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that serves as the WoT entrypoint.
"""

import asyncio
import json
import logging
import warnings

import tornado.gen
from rx import Observable
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from wotpy.support import is_dnssd_supported
from wotpy.utils.utils import handle_observer_finalization
from wotpy.wot.consumed.thing import ConsumedThing
from wotpy.wot.dictionaries.thing import ThingFragment
from wotpy.wot.enums import DiscoveryMethod
from wotpy.wot.exposed.thing import ExposedThing
from wotpy.wot.td import ThingDescription
from wotpy.wot.thing import Thing

DEFAULT_FETCH_TIMEOUT_SECS = 20.0


class WoT(object):
    """The WoT object is the API entry point and it is exposed by an
    implementation of the WoT Runtime. The WoT object does not expose
    properties, only methods for discovering, consuming and exposing a Thing."""

    def __init__(self, servient):
        self._servient = servient
        self._logr = logging.getLogger(__name__)

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

        if not td:
            raise RuntimeError

        fragment_dict = thing_filter.fragment if thing_filter.fragment else {}

        return all(item in td.to_dict().items() for item in fragment_dict.items())

    def _build_local_discover_observable(self, thing_filter):
        """Builds an Observable to discover Things using the local method."""

        found_tds = [
            ThingDescription.from_thing(exposed_thing.thing).to_str()
            for exposed_thing in self._servient.exposed_things
            if self._is_fragment_match(exposed_thing, thing_filter)
        ]

        return Observable.of(*found_tds)

    def _build_dnssd_discover_observable(self, thing_filter, dnssd_find_kwargs):
        """Builds an Observable to discover Things using the multicast method based on DNS-SD."""

        if not is_dnssd_supported():
            warnings.warn(
                "Unsupported DNS-SD multicast discovery",
                UserWarning,
                stacklevel=1,
            )

            return Observable.empty()

        dnssd_find_kwargs = dnssd_find_kwargs if dnssd_find_kwargs else {}

        if not self._servient.dnssd:
            return Observable.empty()

        def subscribe(observer):
            """Browses the Servient services using DNS-SD and retrieves the TDs that match the filters."""

            state = {"stop": False}

            @handle_observer_finalization(observer)
            async def callback():
                address_port_pairs = await self._servient.dnssd.find(
                    **dnssd_find_kwargs
                )

                def build_pair_url(idx, path=None):
                    addr, port = address_port_pairs[idx]
                    base = "http://{}:{}".format(addr, port)
                    path = path if path else ""
                    return "{}/{}".format(base, path.strip("/"))

                http_client = AsyncHTTPClient()

                catalogue_resps = [
                    http_client.fetch(build_pair_url(idx))
                    for idx in range(len(address_port_pairs))
                ]

                wait_iter = tornado.gen.WaitIterator(*catalogue_resps)

                while not wait_iter.done() and not state["stop"]:
                    try:
                        catalogue_resp = await wait_iter.next()
                    except Exception as ex:
                        self._logr.warning(
                            "Exception on HTTP request to TD catalogue: {}".format(ex)
                        )
                    else:
                        catalogue = json.loads(catalogue_resp.body)

                        if state["stop"]:
                            return

                        td_resps = await asyncio.gather(
                            *[
                                http_client.fetch(
                                    build_pair_url(wait_iter.current_index, path=path)
                                )
                                for thing_id, path in catalogue.items()
                            ]
                        )

                        tds = [ThingDescription(td_resp.body) for td_resp in td_resps]

                        tds_filtered = [
                            td
                            for td in tds
                            if self._is_fragment_match(td, thing_filter)
                        ]

                        [observer.on_next(td.to_str()) for td in tds_filtered]

            def unsubscribe():
                state["stop"] = True

            asyncio.get_event_loop().call_soon(callback)

            return unsubscribe

        return Observable.create(subscribe)

    def discover(self, thing_filter, dnssd_find_kwargs=None):
        """Starts the discovery process that will provide ThingDescriptions
        that match the optional argument filter of type ThingFilter."""

        supported_methods = [
            DiscoveryMethod.ANY,
            DiscoveryMethod.LOCAL,
            DiscoveryMethod.MULTICAST,
        ]

        if thing_filter.method not in supported_methods:
            err = NotImplementedError("Unsupported discovery method")
            return Observable.throw(err)

        if thing_filter.query:
            err = NotImplementedError(
                "Queries are not supported yet (please use filter.fragment)"
            )

            return Observable.throw(err)

        observables = []

        if thing_filter.method in [DiscoveryMethod.ANY, DiscoveryMethod.LOCAL]:
            observables.append(self._build_local_discover_observable(thing_filter))

        if thing_filter.method in [DiscoveryMethod.ANY, DiscoveryMethod.MULTICAST]:
            observables.append(
                self._build_dnssd_discover_observable(thing_filter, dnssd_find_kwargs)
            )

        return Observable.merge(*observables)

    @classmethod
    async def fetch(cls, url, timeout_secs=None):
        """Accepts an url argument and returns a Future
        that resolves with a Thing Description string."""

        timeout_secs = timeout_secs or DEFAULT_FETCH_TIMEOUT_SECS

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, request_timeout=timeout_secs)

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
        exposed_thing = ExposedThing(servient=self._servient, thing=thing)
        self._servient.add_exposed_thing(exposed_thing)

        return exposed_thing

    async def produce_from_url(self, url, timeout_secs=None):
        """Return a Future that resolves to an ExposedThing created
        from the thing description retrieved from the given URL."""

        td_str = await self.fetch(url, timeout_secs=timeout_secs)
        exposed_thing = self.produce(td_str)

        return exposed_thing

    async def consume_from_url(self, url, timeout_secs=None):
        """Return a Future that resolves to a ConsumedThing created
        from the thing description retrieved from the given URL."""

        td_str = await self.fetch(url, timeout_secs=timeout_secs)
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
