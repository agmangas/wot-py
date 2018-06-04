#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the abstract client interface.
"""

from abc import ABCMeta, abstractmethod


class ProtocolClientException(Exception):
    """"""

    pass


class BaseProtocolClient(object):
    """Base protocol client class.
    This is the interface that must be implemented by all client classes."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def invoke_action(self, td, name, *args, **kwargs):
        """Invokes an Action on a remote Thing.
        Returns a Future."""

        raise NotImplementedError()

    @abstractmethod
    def write_property(self, td, name, value):
        """Updates the value of a Property on a remote Thing.
        Returns a Future."""

        raise NotImplementedError()

    @abstractmethod
    def read_property(self, td, name):
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
    def on_td_change(self, td):
        """Subscribes to Thing Description changes on a remote Thing.
        Returns an Observable."""

        raise NotImplementedError()
