try:
    import logging

    import coloredlogs

    coloredlogs.install(level=logging.DEBUG)
    logging.getLogger("faker").level = logging.WARNING
except ImportError:
    pass
