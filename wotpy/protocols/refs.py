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
