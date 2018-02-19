#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Abstract interface for exposed Things.
"""

from abc import ABCMeta, abstractmethod


class AbstractExposedThing(object):
    """Interface for exposed Things."""

    __metaclass__ = ABCMeta

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def register(self, directory=None):
        pass

    @abstractmethod
    def unregister(self, directory=None):
        pass

    @abstractmethod
    def emit_event(self, event_name, payload):
        pass

    @abstractmethod
    def add_property(self, property_init):
        pass

    @abstractmethod
    def remove_property(self, name):
        pass

    @abstractmethod
    def add_action(self, action):
        pass

    @abstractmethod
    def remove_action(self, name):
        pass

    @abstractmethod
    def add_event(self, event):
        pass

    @abstractmethod
    def remove_event(self, name):
        pass

    @abstractmethod
    def set_action_handler(self, action_handler, action_name=None):
        pass

    @abstractmethod
    def set_property_read_handler(self, read_handler, property_name=None):
        pass

    @abstractmethod
    def set_property_write_handler(self, write_handler, property_name=None):
        pass
