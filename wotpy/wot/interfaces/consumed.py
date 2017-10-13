#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod, abstractproperty


class BaseConsumedThing(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def url(self):
        pass

    @abstractproperty
    def description(self):
        pass

    @abstractmethod
    def invoke_action(self, name, *args, **kwargs):
        pass

    @abstractmethod
    def set_property(self, name, value):
        pass

    @abstractmethod
    def get_property(self, name):
        pass

    @abstractmethod
    def add_listener(self, event_name, listener):
        pass

    @abstractmethod
    def remove_listener(self, event_name, listener):
        pass

    @abstractmethod
    def remove_all_listeners(self, event_name=None):
        pass

    @abstractmethod
    def observe(self, name, request_type):
        pass
