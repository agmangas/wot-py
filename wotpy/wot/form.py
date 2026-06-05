#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2018 CTIC Centro Tecnologico
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# SPDX-License-Identifier: MIT

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
            tuple(self.op) if isinstance(self.op, list) else self.op
        ))
