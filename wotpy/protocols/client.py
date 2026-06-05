#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
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
Class that represents the abstract client interface.
"""

from abc import ABCMeta, abstractmethod


class BaseProtocolClient(object):
    """Base protocol client class.
    This is the interface that must be implemented by all client classes."""

    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def protocol(self):
        """Protocol of this client instance.
        A member of the Protocols enum."""

        raise NotImplementedError()

    @abstractmethod
    def is_supported_interaction(self, td, name):
        """Returns True if the any of the Forms for the Interaction
        with the given name is supported in this Protocol Binding client."""

        raise NotImplementedError()

    @abstractmethod
    def invoke_action(self, td, name, input_value, timeout=None):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        raise NotImplementedError()

    @abstractmethod
    def write_property(self, td, name, value, timeout=None):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        raise NotImplementedError()

    @abstractmethod
    def read_property(self, td, name, timeout=None):
        """Reads the value of a Property on a remote Thing.
        Returns a Future."""

        raise NotImplementedError()

    @abstractmethod
    def on_event(self, td, name):
        """Subscribes to an event on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError()

    @abstractmethod
    def on_property_change(self, td, name):
        """Subscribes to property changes on a remote Thing.
        Returns an Observable"""

        raise NotImplementedError()

    @abstractmethod
    def on_td_change(self, url):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError()
