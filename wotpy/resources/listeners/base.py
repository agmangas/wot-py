#!/usr/bin/env python
# -*- coding: utf-8 -*-


class BaseResourceListener(object):
    """Base resource listener."""

    def on_read(self):
        """Called to handle resource reads.
        Returns a future that resolves to the read value."""

        raise NotImplementedError()

    def on_write(self, value):
        """Called to handle resource writes.
        Returns a future that resolves to void when the write is finished."""

        raise NotImplementedError()

    def on_invoke(self, invocation_args):
        """Called to handle resource invocations.
        Returns a future that resolves to the invocation response."""

        raise NotImplementedError()
