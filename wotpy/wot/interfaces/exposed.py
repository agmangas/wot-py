#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod


class BaseExposedThing(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def add_property(self, the_property):
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
    def on_retrieve_property(self, handler):
        pass

    @abstractmethod
    def on_update_property(self, handler):
        pass

    @abstractmethod
    def on_invoke_action(self, handler):
        pass

    @abstractmethod
    def on_observe(self, handler):
        pass

    @abstractmethod
    def register(self, directory=None):
        pass

    @abstractmethod
    def unregister(self, directory=None):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def emit_event(self, event_name, payload):
        pass
