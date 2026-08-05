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
Class that represents a Thing consumed by a servient.
"""

from reactivex.scheduler.eventloop import IOLoopScheduler
from tornado import ioloop

from wotpy.wot.consumed.interaction_map import (
    ConsumedThingActionDict,
    ConsumedThingEventDict,
    ConsumedThingPropertyDict
)


class ConsumedThing:
    """An entity that serves to interact with a Thing.
    An application uses this class when it acts as a *client* of the Thing."""

    def __init__(self, servient, td):
        self._servient = servient
        self._td = td

    def __str__(self):
        return "<{}> {}".format(self.__class__.__name__, self.td.id)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the private ThingFragment instance before propagating the exception."""

        return getattr(self.td.to_thing_fragment(), name)

    @property
    def servient(self):
        """Returns the Servient that contains this Consumed Thing."""

        return self._servient

    @property
    def td(self):
        """Returns the ThingDescription instance that represents
        the TD that this Consumed Thing is based on."""

        return self._td

    async def invoke_action(
        self, name, input_value=None, timeout=None, client_kwargs=None
    ):
        """Takes the Action name from the name argument and the list of parameters,
        then requests from the underlying platform and the Protocol Bindings to invoke
        the Action on the remote Thing and return the result.
        Returns a Future that resolves with the return value or rejects with an Error.
        """

        client = self.servient.select_client(self.td, name)
        client_kwargs = client_kwargs if client_kwargs else {}

        result = await client.invoke_action(
            self.td,
            name,
            input_value,
            timeout=timeout,
            **client_kwargs.get(client.protocol, {})
        )

        return result

    async def write_property(self, name, value, timeout=None, client_kwargs=None):
        """Takes the Property name as the name argument and the new value as the value
        argument, then requests from the underlying platform and the Protocol Bindings
        to update the Property on the remote Thing and return the result.
        Returns a Future that resolves on success or rejects with an Error."""

        client = self.servient.select_client(self.td, name)
        client_kwargs = client_kwargs if client_kwargs else {}

        await client.write_property(
            self.td,
            name,
            value,
            timeout=timeout,
            **client_kwargs.get(client.protocol, {})
        )

    async def read_property(self, name, timeout=None, client_kwargs=None):
        """Takes the Property name as the name argument, then requests from the
        underlying platform and the Protocol Bindings to retrieve the Property
        on the remote Thing and return the result.
        Returns a Future that resolves with the Property value or rejects with an Error.
        """

        client = self.servient.select_client(self.td, name)
        client_kwargs = client_kwargs if client_kwargs else {}

        value = await client.read_property(
            self.td, name, timeout=timeout, **client_kwargs.get(client.protocol, {})
        )

        return value

    def on_event(self, name, client_kwargs=None):
        """Returns an Observable for the Event specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        client = self.servient.select_client(self.td, name)
        client_kwargs = client_kwargs if client_kwargs else {}

        return client.on_event(self.td, name, **client_kwargs.get(client.protocol, {}))

    def on_property_change(self, name, client_kwargs=None):
        """Returns an Observable for the Property specified in the name argument,
        allowing subscribing to and unsubscribing from notifications."""

        client = self.servient.select_client(self.td, name)
        client_kwargs = client_kwargs if client_kwargs else {}

        return client.on_property_change(
            self.td, name, **client_kwargs.get(client.protocol, {})
        )

    def on_td_change(self):
        """Returns an Observable, allowing subscribing to and unsubscribing
        from notifications to the Thing Description."""

        raise NotImplementedError()

    @property
    def properties(self):
        """Returns a dictionary of ThingProperty items."""

        return ConsumedThingPropertyDict(consumed_thing=self)

    @property
    def actions(self):
        """Returns a dictionary of ThingAction items."""

        return ConsumedThingActionDict(consumed_thing=self)

    @property
    def events(self):
        """Returns a dictionary of ThingEvent items."""

        return ConsumedThingEventDict(consumed_thing=self)

    @property
    def links(self):
        """Represents a dictionary of WebLink items."""

        raise NotImplementedError()

    def subscribe(self, *args, **kwargs):
        """Subscribes to changes on the TD of this thing."""

        observable = self.on_td_change()
        loop = ioloop.IOLoop.current()
        scheduler = IOLoopScheduler(loop)
        kwargs["scheduler"] = scheduler

        return observable.subscribe(*args, **kwargs)
