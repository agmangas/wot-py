import logging
import os

logger_base = logging.getLogger(__name__)
logger_base.addHandler(logging.NullHandler())

if os.environ.get("WOTPY_ENABLE_UVLOOP", False):
    try:
        import asyncio
        import uvloop

        logger_base.warning("Installing uvloop (this is an experimental feature)")
        uvloop.install()
    except ImportError:
        logger_base.warning("Error installing uvloop (cannot import package)")
