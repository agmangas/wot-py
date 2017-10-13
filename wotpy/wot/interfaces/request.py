#!/usr/bin/env python
# -*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod, abstractproperty


class BaseRequest(object):
    __metaclass__ = ABCMeta

    @abstractproperty
    def type(self):
        pass

    @abstractproperty
    def from_address(self):
        pass

    @abstractproperty
    def name(self):
        pass

    @abstractproperty
    def options(self):
        pass

    @abstractproperty
    def data(self):
        pass

    @abstractmethod
    def respond(self, response):
        pass

    @abstractmethod
    def respond_with_error(self, error):
        pass
