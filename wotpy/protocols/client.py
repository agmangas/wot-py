#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
