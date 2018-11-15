#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the form entities exposed by interactions.
"""

from wotpy.wot.dictionaries.link import FormDict


class Form(object):
    """Communication metadata where a service can be accessed by a client application."""

    def __init__(self, interaction, protocol, form_dict=None, **kwargs):
        self._interaction = interaction
        self._protocol = protocol
        self._form_dict = form_dict if form_dict else FormDict(**kwargs)

    def __getattr__(self, name):
        """Search for members that raised an AttributeError in
        the internal Form init dict before propagating the exception."""

        return getattr(self._form_dict, name)

    @property
    def form_dict(self):
        """The Form dictionary of this Form."""

        return self._form_dict

    @property
    def interaction(self):
        """Interaction that contains this Form."""

        return self._interaction

    @property
    def protocol(self):
        """Form protocol."""

        return self._protocol

    @property
    def id(self):
        """Returns the ID of this Form.
        The ID is a hash that is based on the Form attributes.
        No two Forms with the same ID may exist within the same Interaction.
        The ID of a Form could change during its lifetime if some attributes are updated."""

        return hash((
            self.protocol,
            self.href,
            self.content_type,
            self.op
        ))
