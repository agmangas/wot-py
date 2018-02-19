#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Abstract interface for consumed Things.
"""

from abc import ABCMeta, abstractmethod, abstractproperty


class AbstractConsumedThing(object):
    """Interface for consumed Things.
    All Things (both consumed and exposed) implement this."""

    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        pass

    @abstractmethod
    def get_thing_description(self):
        pass

    @abstractmethod
    def invoke_action(self, name, *args, **kwargs):
        pass

    @abstractmethod
    def write_property(self, name, value):
        pass

    @abstractmethod
    def read_property(self, name):
        pass

    @abstractmethod
    def on_event(self, name):
        pass

    @abstractmethod
    def on_property_change(self, name):
        pass

    @abstractmethod
    def on_td_change(self):
        pass
