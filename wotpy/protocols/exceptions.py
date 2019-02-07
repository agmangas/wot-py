#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
