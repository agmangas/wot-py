#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the form entities exposed by interactions.
"""

from wotpy.wot.dictionaries import FormDictionary


class Form(object):
    """Communication metadata where a service can be accessed by a client application."""

    def __init__(self, interaction, protocol, form_dict=None, **kwargs):
        self.interaction = interaction
        self.protocol = protocol
        self._form_dict = form_dict if form_dict else FormDictionary(**kwargs)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal FormDictionary before propagating the exception."""

        return self._form_dict.__getattribute__(name)

    @property
    def id(self):
        """Returns the ID of this Form.
        The ID is a hash that is based on its attributes and the ID of its Interaction.
        No two Forms with the same ID may exist within the same Interaction."""

        return hash((
            self.interaction.id,
            self.protocol,
            self.href,
            self.media_type,
            self.rel
        ))
