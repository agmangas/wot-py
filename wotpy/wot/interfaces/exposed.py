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
    def expose(self):
        pass

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def emit_event(self, event_name, payload):
        pass

    @abstractmethod
    def add_property(self, name, property_init):
        pass

    @abstractmethod
    def remove_property(self, name):
        pass

    @abstractmethod
    def add_action(self, name, action_init):
        pass

    @abstractmethod
    def remove_action(self, name):
        pass

    @abstractmethod
    def add_event(self, name, event_init):
        pass

    @abstractmethod
    def remove_event(self, name):
        pass

    @abstractmethod
    def set_action_handler(self, name, action_handler):
        pass

    @abstractmethod
    def set_property_read_handler(self, name, read_handler):
        pass

    @abstractmethod
    def set_property_write_handler(self, write_handler, property_name=None):
        pass
