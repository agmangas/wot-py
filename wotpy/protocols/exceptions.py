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
Exceptions raised by the protocol binding implementations.
"""


class ProtocolClientException(Exception):
    """Base Exceptions raised by clients of the protocol binding implementations."""

    DEFAULT_MSG = "Protocol client error"

    def __init__(self, *args, **kwargs):
        if not (args or kwargs):
            args = (self.DEFAULT_MSG,)

        super(ProtocolClientException, self).__init__(*args, **kwargs)


class FormNotFoundException(ProtocolClientException):
    """Exception raised when a form for a given protocol
    binding could not be found in a Thing Description."""

    DEFAULT_MSG = "Protocol Form not found in TD"


class ClientRequestTimeout(ProtocolClientException):
    """Exception raised when a protocol client request reaches the timeout."""

    DEFAULT_MSG = "Timeout in protocol client request"
