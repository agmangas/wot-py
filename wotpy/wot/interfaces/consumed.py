#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Abstract interface for consumed Things.
"""

from abc import ABCMeta, abstractmethod


class AbstractConsumedThing(object):
    """Interface for consumed Things.
    All Things (both consumed and exposed) implement this."""

    __metaclass__ = ABCMeta

    @property
    @abstractmethod
    def properties(self):
        pass

    @property
    @abstractmethod
    def actions(self):
        pass

    @property
    @abstractmethod
    def events(self):
        pass

    @property
    @abstractmethod
    def links(self):
        pass

    @abstractmethod
    def subscribe(self):
        pass
