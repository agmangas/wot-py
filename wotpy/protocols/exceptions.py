#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Exceptions raised by the protocol binding implementations.
"""


class ProtocolClientException(Exception):
    """Base Exceptions raised by clients of the protocol binding implementations."""

    pass


class FormNotFoundException(ProtocolClientException):
    """Exception raised when a form for a given protocol
    binding could not be found in a Thing Description."""

    pass


class ClientRequestTimeout(ProtocolClientException):
    """Exception raised when a protocol client request reaches the timeout."""

    pass
