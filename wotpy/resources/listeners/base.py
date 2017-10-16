#!/usr/bin/env python
# -*- coding: utf-8 -*-

# noinspection PyCompatibility
from concurrent.futures import Future


class BaseResourceListener(object):
    """Base resource listener."""

    @classmethod
    def _build_not_implemented_future(cls):
        """Returns a Future that raises NotImplementedError."""

        future = Future()
        future.set_exception(NotImplementedError())

        return future

    def on_read(self):
        """Called to handle resource reads.
        Returns a future that resolves to the read value."""

        return self._build_not_implemented_future()

    def on_write(self, value):
        """Called to handle resource writes.
        Returns a future that resolves to void when the write is finished."""

        return self._build_not_implemented_future()

    def on_invoke(self, invocation_args):
        """Called to handle resource invocations.
        Returns a future that resolves to the invocation response."""

        return self._build_not_implemented_future()

    def on_observe(self, name, request_type):
        """Called to handle resource observations.
        Returns a future that resolves to void when the observation process has finished."""

        return self._build_not_implemented_future()
