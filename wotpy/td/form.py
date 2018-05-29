#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that represents the form entities exposed by interactions.
"""


class Form(object):
    """Communication metadata where a service can be accessed by a client application."""

    def __init__(self, interaction, protocol, **kwargs):
        self.interaction = interaction
        self.protocol = protocol
        self.href = kwargs.pop("href")
        self.media_type = kwargs.get("media_type", "application/json")
        self.rel = kwargs.get("rel")
        self.security = kwargs.get("security")

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
