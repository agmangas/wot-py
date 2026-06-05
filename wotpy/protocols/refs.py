# Copyright (c) 2019 CTIC Centro Tecnologico
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

import logging


class ConnRefCounter(object):
    """A simple connection reference counter to keep
    track of active connections and enable reuse."""

    def __init__(self):
        self._counter = {}
        self._logr = logging.getLogger(__name__)

    def increase(self, conn_id, ref_id):
        """Increases the reference counter for the connection."""

        if conn_id not in self._counter:
            self._counter[conn_id] = set()

        self._counter[conn_id].add(ref_id)

        self._logr.debug("Added ref {} to conn <{}> (current: {})".format(
            ref_id, conn_id, len(self._counter[conn_id])))

    def decrease(self, conn_id, ref_id):
        """Decreases the reference counter for the connection."""

        if conn_id not in self._counter:
            self._logr.warning("Attempted to decrease ref of unknown conn: {}".format(conn_id))
            return

        try:
            self._counter[conn_id].remove(ref_id)

            self._logr.debug("Removed ref {} from conn <{}> (current: {})".format(
                ref_id, conn_id, len(self._counter[conn_id])))
        except KeyError:
            self._logr.warning("Attempted to remove unknown reference: {}".format(ref_id))

    def has_any(self, conn_id):
        """Returns True if the connection has any references pointing to it."""

        return conn_id in self._counter and len(self._counter[conn_id])
