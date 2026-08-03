import asyncio
import logging

logr = logging.getLogger(__name__)

SUB_DELAY = 2.0

TIMEOUT_PROP_READ = 120.0
TIMEOUT_PROP_WRITE = 120.0
TIMEOUT_ACTION_INVOCATION = 1800.0
TIMEOUT_HARD_FACTOR = 1.2


def build_prop_read_proxy(consumed_thing, name):
    """Factory for proxy Property read handlers."""

    async def _proxy():
        timeout_soft = TIMEOUT_PROP_READ
        timeout_hard = TIMEOUT_PROP_READ * TIMEOUT_HARD_FACTOR

        awaitable = consumed_thing.properties[name].read(timeout=timeout_soft)

        return await asyncio.wait_for(awaitable, timeout=timeout_hard)

    return _proxy


def build_prop_write_proxy(consumed_thing, name):
    """Factory for proxy Property write handlers."""

    async def _proxy(val):
        timeout_soft = TIMEOUT_PROP_WRITE
        timeout_hard = TIMEOUT_PROP_WRITE * TIMEOUT_HARD_FACTOR

        awaitable = consumed_thing.properties[name].write(val, timeout=timeout_soft)

        await asyncio.wait_for(awaitable, timeout=timeout_hard)

    return _proxy


def build_action_invoke_proxy(consumed_thing, name):
    """Factory for proxy Action invocation handlers."""

    async def _proxy(params):
        timeout_soft = TIMEOUT_ACTION_INVOCATION
        timeout_hard = TIMEOUT_ACTION_INVOCATION * TIMEOUT_HARD_FACTOR

        awaitable = consumed_thing.actions[name].invoke(params.get('input'), timeout=timeout_soft)

        return await asyncio.wait_for(awaitable, timeout=timeout_hard)

    return _proxy


def subscribe_event(consumed_thing, exposed_thing, name):
    """Creates and maintains a subscription to the given Event, recreating it on error."""

    state = {'sub': None}

    def _on_next(item):
        logr.info("{}".format(item))
        exposed_thing.events[name].emit(item.data)

    def _on_completed():
        logr.info("Completed (Event {})".format(name))

    def _on_error(err):
        logr.warning("Error (Event {}) :: {}".format(name, err))

        try:
            logr.warning("Disposing of erroneous subscription")
            state['sub'].dispose()
        except Exception as ex:
            logr.warning("Error disposing: {}".format(ex), exc_info=True)

        def _sub():
            logr.warning("Recreating subscription")
            state['sub'] = consumed_thing.events[name].subscribe(
                on_next=_on_next,
                on_completed=_on_completed,
                on_error=_on_error)

        logr.warning("Re-creating subscription in {} seconds".format(SUB_DELAY))

        asyncio.get_event_loop().call_later(SUB_DELAY, _sub)

    state['sub'] = consumed_thing.events[name].subscribe(
        on_next=_on_next,
        on_completed=_on_completed,
        on_error=_on_error)
